import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.schemas import ApiModel

logger = logging.getLogger(__name__)
PROBLEM_JSON = "application/problem+json"


# --- Domain errors: services raise these, never HTTPException -------------------------


class AppError(Exception):
    status = 500
    code = "internal_error"
    title = "Internal Server Error"

    def __init__(self, detail: str | None = None, *, code: str | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        if code:
            self.code = code


class BadRequestError(AppError):
    status, code, title = 400, "bad_request", "Bad Request"


class UnauthenticatedError(AppError):
    status, code, title = 401, "unauthenticated", "Unauthenticated"


class PermissionDeniedError(AppError):
    status, code, title = 403, "forbidden", "Forbidden"


class NotFoundError(AppError):
    status, code, title = 404, "not_found", "Not Found"


class ConflictError(AppError):
    status, code, title = 409, "conflict", "Conflict"


class ExternalServiceError(AppError):
    """An upstream API (Google, Anthropic) failed or could not be reached."""

    status, code, title = 502, "external_service_error", "Bad Gateway"


class GoogleReauthRequiredError(UnauthenticatedError):
    """Stored Google credentials are missing, revoked or undecryptable."""

    code = "google_reauth_required"

    def __init__(self, detail: str = "Reconnect your Google account.") -> None:
        super().__init__(detail)


# --- RFC 9457 Problem Details ----------------------------------------------------------


class FieldError(ApiModel):
    field: str  # dotted camelCase path matching the request JSON, e.g. "settings.model"
    message: str
    code: str


class ProblemDetail(ApiModel):
    type: str = "about:blank"
    title: str
    status: int
    code: str
    detail: str | None = None
    instance: str | None = None
    errors: list[FieldError] | None = None


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    s: {"model": ProblemDetail, "content": {PROBLEM_JSON: {}}}
    for s in (400, 401, 403, 404, 409, 422, 500, 502)
}


def _problem(
    request: Request, problem: ProblemDetail, headers: dict[str, str] | None = None
) -> JSONResponse:
    problem.instance = problem.instance or request.url.path
    return JSONResponse(
        status_code=problem.status,
        content=problem.model_dump(mode="json", by_alias=True, exclude_none=True),
        media_type=PROBLEM_JSON,
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error(request: Request, exc: AppError) -> JSONResponse:
        return _problem(
            request,
            ProblemDetail(title=exc.title, status=exc.status, code=exc.code, detail=exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            FieldError(
                # loc is e.g. ("body", "settings", "model"); keys are the aliases the client sent
                field=".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]),
                message=e["msg"],
                code=e["type"],
            )
            for e in exc.errors()
        ]
        return _problem(
            request,
            ProblemDetail(
                title="Unprocessable Content",
                status=422,
                code="validation_error",
                detail="Request validation failed",
                errors=errors,
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem(
            request,
            ProblemDetail(
                title=str(exc.detail) if exc.status_code < 500 else "Internal Server Error",
                status=exc.status_code,
                code=f"http_{exc.status_code}",
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _problem(
            request,
            ProblemDetail(title="Internal Server Error", status=500, code="internal_error"),
        )
