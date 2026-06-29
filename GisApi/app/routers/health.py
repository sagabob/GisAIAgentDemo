from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from app.database import ping_database
from app.dependencies import get_mongo_client
from app.exceptions import DatabaseUnavailableError

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    responses={
        200: {
            "description": "API and database are healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "database": "ok"},
                }
            },
        },
        503: {"description": "Database is unavailable"},
    },
)
async def health(
    mongo_client: AsyncIOMotorClient = Depends(get_mongo_client),
) -> dict[str, str]:
    try:
        await ping_database(mongo_client)
    except Exception as exc:
        raise DatabaseUnavailableError("MongoDB ping failed") from exc
    return {"status": "ok", "database": "ok"}
