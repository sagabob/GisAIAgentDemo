import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from config import get_gis_api_base_url, get_settings
from dependencies import get_session_store
from logging_config import RequestLoggingMiddleware, configure_logging
from schemas import ChatRequest, ChatResponse, ResetRequest
from session_store import SessionStore

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.session_store = SessionStore()
    settings = get_settings()
    logger.info("GIS Agent API started (gisApi=%s)", settings.gis_api_url)
    yield
    app.state.session_store.close_all()
    logger.info("GIS Agent API stopped")


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="GIS Agent API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "gisApi": get_gis_api_base_url()}

    @app.post("/chat", response_model=ChatResponse)
    async def chat(
        payload: ChatRequest,
        sessions: SessionStore = Depends(get_session_store),
    ) -> ChatResponse:
        session_id = payload.session_id or str(uuid.uuid4())
        agent = sessions.get_or_create(session_id)
        result = agent.ask_with_metadata(payload.message)
        return ChatResponse(
            answer=result.answer,
            places=result.places,
            total=result.total,
            session_id=session_id,
        )

    @app.post("/chat/reset")
    async def reset_chat(
        payload: ResetRequest,
        sessions: SessionStore = Depends(get_session_store),
    ) -> dict[str, str]:
        sessions.reset(payload.session_id)
        return {"status": "reset"}

    return app


app = create_app()
