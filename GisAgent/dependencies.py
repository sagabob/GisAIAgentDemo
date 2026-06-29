from starlette.requests import Request

from session_store import SessionStore


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.session_store
