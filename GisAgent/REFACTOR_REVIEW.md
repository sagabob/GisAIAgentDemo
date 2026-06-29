# GisAgent Refactor Review

Refactor aligned with **GisApi** patterns: typed settings, clearer module boundaries, session lifecycle, and tests. **No API contract changes** — `POST /chat`, `POST /chat/reset`, and `GET /health` behave the same for GisPortal.

---

## Summary of changes

| Area | Before | After |
|------|--------|-------|
| Configuration | `os.getenv()` helpers | `pydantic-settings` `Settings` class |
| CORS | In-app middleware | Removed (configured in Azure) |
| Server | Flat `server.py` + global `_sessions` | `create_app()`, lifespan, `SessionStore` |
| Schemas | Inline in `server.py` | `schemas.py` (`ChatRequest`, `ChatResponse`, `AgentResult`) |
| Agent helpers | Private functions in `agent.py` | `places.py` (extract, dedupe, summary) |
| System prompt | In `agent.py` | `prompts.py` |
| Tool dispatch | Long `if` chain | `TOOL_HANDLERS` dict in `tools.py` |
| Sessions | Never closed on shutdown | `SessionStore.close_all()` in lifespan |
| Logging | None | Request logging + `X-Request-ID` |
| Duplicate logic | `server.py` re-called `_build_places_answer` | Agent returns final `AgentResult` only |
| Tests | None | `pytest` unit + API tests |

---

## Project structure (after)

```
GisAgent/
├── agent.py              # GisAgent orchestration (OpenAI + tools)
├── api_client.py         # HTTP client for GIS API
├── config.py             # Settings (pydantic-settings)
├── dependencies.py       # FastAPI Depends(get_session_store)
├── logging_config.py     # Request logging middleware
├── places.py             # Place extraction, dedupe, summary text
├── prompts.py            # SYSTEM_PROMPT
├── schemas.py            # API request/response models
├── session_store.py      # Per-session GisAgent instances
├── tools.py              # Tool definitions + TOOL_HANDLERS dispatch
├── server.py             # create_app(), routes, lifespan
├── chat.py               # CLI entry point
├── tests/
│   ├── conftest.py
│   ├── test_places.py
│   ├── test_tools.py
│   └── test_server.py
├── requirements.txt
├── requirements-dev.txt
└── REFACTOR_REVIEW.md
```

---

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for chat completions |
| `GIS_API_BASE_URL` | Yes | — | GIS Places API base URL |
| `MAX_TOOL_ROUNDS` | No | `5` | Max tool-call loops per message |
| `LOG_LEVEL` | No | `INFO` | Python log level |

---

## Session lifecycle

```python
# lifespan in server.py
app.state.session_store = SessionStore()
yield
app.state.session_store.close_all()  # closes httpx clients
```

Routes receive the store via `Depends(get_session_store)` instead of a module-level dict.

---

## Agent result flow

```
POST /chat
  → SessionStore.get_or_create(session_id)
  → GisAgent.ask_with_metadata(message)
       → OpenAI tool loop
       → places.extract / dedupe / build_places_answer
  → ChatResponse(answer, places, total, session_id)
```

The portal still receives `{ answer, places, total, session_id }` unchanged.

---

## Running locally

```powershell
cd GisAgent
pip install -r requirements.txt
uvicorn server:app --host 127.0.0.1 --port 8001 --reload
```

CLI:

```powershell
python chat.py
```

---

## Running tests

```powershell
cd GisAgent
pip install -r requirements-dev.txt
pytest
```

No OpenAI or GIS API calls required — tests use mocks.

---

## Breaking changes

**None** for GisPortal or existing API consumers.

---

## Review checklist

- [ ] `.env` has `OPENAI_API_KEY`
- [ ] Restart agent: `uvicorn server:app --port 8001 --reload`
- [ ] Run `pytest`
- [ ] Test intelligent search in GisPortal
- [ ] Configure CORS on Azure (not in the app)
