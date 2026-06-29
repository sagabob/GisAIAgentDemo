import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class DatabaseUnavailableError(Exception):
    pass


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PyMongoError)
    async def pymongo_error_handler(_: Request, exc: PyMongoError) -> JSONResponse:
        logger.exception("MongoDB error")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Database operation failed"},
        )

    @app.exception_handler(DatabaseUnavailableError)
    async def database_unavailable_handler(_: Request, exc: DatabaseUnavailableError) -> JSONResponse:
        logger.warning("Database unavailable: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Database is unavailable"},
        )
