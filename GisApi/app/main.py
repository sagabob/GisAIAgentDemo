import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import Settings, get_settings
from app.database import ensure_indexes
from app.exceptions import register_exception_handlers
from app.logging_config import RequestLoggingMiddleware, configure_logging
from app.routers import categories, health, places, pointofinterest

logger = logging.getLogger(__name__)

API_V1_PREFIX = "/api/v1"


def _register_routes(app: FastAPI, router: APIRouter, *, prefix: str = "") -> None:
    app.include_router(router, prefix=prefix)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    app.state.settings = settings
    app.state.mongo_client = AsyncIOMotorClient(settings.mongodb_uri)

    try:
        await ensure_indexes(app.state.mongo_client, settings)
    except Exception:
        logger.exception("Failed to ensure database indexes")

    logger.info("GIS Places API started (db=%s)", settings.db_name)
    yield

    app.state.mongo_client.close()
    logger.info("GIS Places API stopped")


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title="GIS Places API",
        description="Search Christchurch place names by name or category, sorted alphabetically or by rating.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)
    register_exception_handlers(app)

    for router in (health.router, categories.router, places.router, pointofinterest.router):
        _register_routes(app, router)
        _register_routes(app, router, prefix=API_V1_PREFIX)

    return app


app = create_app()
