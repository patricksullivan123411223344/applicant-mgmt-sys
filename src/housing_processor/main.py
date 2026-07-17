from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from housing_processor import __version__
from housing_processor.bootstrap import build_container
from housing_processor.observability.logging import configure_logging, get_logger
from housing_processor.presentation.api.errors import register_exception_handlers
from housing_processor.presentation.api.routes import (
    applicants,
    applications,
    exports,
    groups,
    reviews,
    system,
)

logger = get_logger(__name__)

# Repo root: .../llm_read_write_sys (parent of src/)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIR = _REPO_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    container = build_container()
    app.state.container = container
    logger.info("application_started", extra={"environment": container.settings.environment})
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Student Housing Application Processing System",
        version=__version__,
        lifespan=lifespan,
    )
    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-Id")
        if request_id:
            request.state.request_id = request_id
        response = await call_next(request)
        if hasattr(request.state, "request_id"):
            response.headers["X-Request-Id"] = request.state.request_id
        return response

    @app.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready(request: Request) -> JSONResponse:
        container = request.app.state.container
        try:
            with container.uow_factory() as uow:
                assert uow.session is not None
                uow.session.execute(text("SELECT 1"))
            storage_ok = container.storage._root.exists()  # noqa: SLF001
            if not storage_ok:
                return JSONResponse(
                    status_code=503,
                    content={"status": "not_ready", "reason": "storage_unavailable"},
                )
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "database_unavailable"},
            )
        return JSONResponse(content={"status": "ready"})

    app.include_router(system.router, prefix="/api/v1")
    app.include_router(applications.router, prefix="/api/v1")
    app.include_router(applicants.router, prefix="/api/v1")
    app.include_router(groups.router, prefix="/api/v1")
    app.include_router(reviews.router, prefix="/api/v1")
    app.include_router(exports.router, prefix="/api/v1")

    # Mount after API routes so /api and /health are not swallowed.
    if _FRONTEND_DIR.is_dir():
        app.mount(
            "/",
            StaticFiles(directory=str(_FRONTEND_DIR), html=True),
            name="frontend",
        )
    else:
        logger.warning("frontend_dir_missing", extra={"path": str(_FRONTEND_DIR)})

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("housing_processor.main:app", host="0.0.0.0", port=8000, reload=True)
