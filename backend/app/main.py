from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from anthropic import AsyncAnthropic
from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.agents.runner import AgentRunner
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import create_tables, dispose_engine, init_engine


def operation_id(route: APIRoute) -> str:
    # Endpoint function names become operationIds (list_emails -> listEmails in codegen).
    # Keep endpoint function names unique across the app.
    return route.name


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    init_engine(settings.database_url)
    create_tables()
    app.state.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
    app.state.agent_runner = AgentRunner(app.state.anthropic)
    yield
    await app.state.anthropic.close()
    dispose_engine()


def create_app() -> FastAPI:
    """No network or database calls here, so tests and export_openapi can build the app."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
        generate_unique_id_function=operation_id,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )
    register_exception_handlers(app)
    if settings.cors_origins:  # only for cross-origin deployments; dev uses the Vite proxy
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-Requested-With"],
        )
    app.include_router(api_router)
    return app


app = create_app()
