from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import close_client
from app.routers import categories, health, places, pointofinterest


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_client()


def create_app() -> FastAPI:
    app = FastAPI(
        title="GIS Places API",
        description="Search Christchurch place names by name or category, sorted alphabetically or by rating.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(categories.router)
    app.include_router(places.router)
    app.include_router(pointofinterest.router)

    return app


app = create_app()
