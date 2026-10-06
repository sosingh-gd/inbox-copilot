from fastapi import APIRouter, Depends

from app.core.errors import COMMON_ERROR_RESPONSES
from app.core.schemas import ApiModel
from app.core.security import require_csrf_header
from app.features.auth.router import router as auth_router
from app.features.chat.router import router as chat_router


api_router = APIRouter(
    prefix="/api/v1",
    responses=COMMON_ERROR_RESPONSES,
    dependencies=[Depends(require_csrf_header)],
)


class HealthRead(ApiModel):
    status: str


@api_router.get("/health", tags=["health"])
def health_check() -> HealthRead:
    return HealthRead(status="ok")


# Add new feature routers here.
api_router.include_router(auth_router)
api_router.include_router(chat_router)
