from agent import GisAgent


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, GisAgent] = {}

    def get_or_create(self, session_id: str) -> GisAgent:
        return self._sessions.setdefault(session_id, GisAgent())

    def reset(self, session_id: str) -> None:
        agent = self._sessions.get(session_id)
        if agent:
            agent.reset()

    def close_all(self) -> None:
        for agent in self._sessions.values():
            agent.close()
        self._sessions.clear()

    @property
    def count(self) -> int:
        return len(self._sessions)
