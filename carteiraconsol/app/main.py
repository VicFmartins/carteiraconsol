from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import ENV_FILE, get_settings
from app.core.exceptions import ApplicationError
from app.core.logging import configure_logging
from app.db.session import init_db
from app.schemas.common import ErrorResponse, ValidationIssue


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.ensure_directories()
    logger.info("Loaded configuration from %s", ENV_FILE)
    if settings.auto_create_tables:
        init_db()
    logger.info("Application startup completed.")
    yield
    logger.info("Application shutdown completed.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.project_name,
        version=settings.app_version,
        description="Event-driven ETL backend for consolidating multi-broker portfolios.",
        lifespan=lifespan,
    )

    @app.exception_handler(ApplicationError)
    async def application_error_handler(_: Request, exc: ApplicationError) -> JSONResponse:
        status_code = 404 if exc.error_code == "resource_not_found" else 422
        payload = ErrorResponse(detail=exc.message, error_code=exc.error_code)
        return JSONResponse(status_code=status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            ValidationIssue(
                field=".".join(str(part) for part in error["loc"] if part not in {"query", "body", "path"}),
                message=error["msg"],
            )
            for error in exc.errors()
        ]
        payload = ErrorResponse(
            detail="Request validation failed.",
            error_code="request_validation_error",
            errors=errors,
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error.", exc_info=exc)
        payload = ErrorResponse(detail="An unexpected error occurred.", error_code="internal_server_error")
        return JSONResponse(status_code=500, content=payload.model_dump())

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
