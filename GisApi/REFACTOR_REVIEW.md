# GisApi Refactor Review

This document summarizes the refactor applied to align **GisApi** with Python and FastAPI best practices. All existing clients (GisPortal, GisAgent) continue to work without changes because legacy routes are preserved.

---

## Summary of changes

| Area | Before | After |
|------|--------|-------|
| Configuration | `os.getenv()` helpers | `pydantic-settings` `Settings` class with validation |
| Database | Lazy global Motor client | Client created in `lifespan`, stored on `app.state` |
| Repositories | Module singletons | Injected via FastAPI `Depends()` |
| Models | Single `models.py` | Split into `app/schemas/` (`common`, `place`, `poi`) |
| Search safety | Raw regex in partial match | `re.escape()` for name and locality |
| Geometry | `list[float]` only | Validates `[lng, lat]` ranges |
| Health | Static `{"status":"ok"}` | MongoDB `ping` + 503 when DB down |
| CORS | Not configured | `CORSMiddleware` from `CORS_ORIGINS` env |
| Logging | None | Structured request logging + `X-Request-ID` |
| Errors | Default only | Handlers for `PyMongoError` and DB unavailable |
| API versioning | None | Duplicate routes under `/api/v1/*` |
| POI IDs | Read-then-insert race | Unique index + retry on `DuplicateKeyError` |
| Tests | None | `pytest` + `httpx` with dependency overrides |
| Tooling | `requirements.txt` only | Added `pyproject.toml` + `ruff` config |

---

## Project structure (after)

```
GisApi/
├── app/
│   ├── main.py              # create_app(), CORS, lifespan, v1 routes
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # ensure_indexes(), ping_database()
│   ├── dependencies.py      # DI + shared query param dependencies
│   ├── exceptions.py        # Global exception handlers
│   ├── logging_config.py    # Request logging middleware
│   ├── queries.py           # MongoDB query builders (regex-safe)
│   ├── models.py            # Backward-compatible re-exports
│   ├── schemas/
│   │   ├── common.py        # Geometry with validation
│   │   ├── place.py         # Place response models
│   │   └── poi.py           # POI CRUD models
│   ├── repositories/
│   │   ├── places.py        # PlaceRepository(collection)
│   │   └── pointofinterest.py
│   └── routers/
│       ├── health.py
│       ├── places.py
│       ├── categories.py
│       └── pointofinterest.py
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_places.py
│   ├── test_geometry.py
│   └── test_poi.py
├── pyproject.toml
├── requirements.txt
└── REFACTOR_REVIEW.md       # This file
```

---

## Configuration (`app/config.py`)

Settings are loaded from the first available env file:

1. `GisApi/.env`
2. `GisApi/app/.env`
3. Repository root `.env`

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MongoDB_URI` | Yes | — | MongoDB connection string |
| `Target_DB_Name` | Yes* | — | Database name |
| `Source_DB_Name` | Yes* | — | Fallback database name |
| `Target_Collection_Name` | No | `ccc_place_names` | Read-only places collection |
| `Demo_Collection_Name` | No | `demo_place_names` | Editable POI collection |
| `CORS_ORIGINS` | No | `*` | Comma-separated origins or `*` |
| `LOG_LEVEL` | No | `INFO` | Python log level |

\* At least one of `Target_DB_Name` or `Source_DB_Name` must be set.

---

## Dependency injection

Repositories receive a MongoDB collection in their constructor. Routes depend on factory functions:

```python
def get_place_repository(
    collection: AsyncIOMotorCollection = Depends(get_places_collection),
) -> PlaceRepository:
    return PlaceRepository(collection)
```

This makes unit tests straightforward via `app.dependency_overrides`.

### Shared query dependencies

Repeated query parameters are centralized in `app/dependencies.py`:

- `pagination_params` → `skip`, `limit`
- `sort_params` → `sort_by`, `sort_order`
- `text_search_filters` → `name`, `category`, `locality`
- `name_search_params` → `place_name`, `exact`, filters

---

## API routes

### Backward compatibility

All original paths remain unchanged:

- `GET /health`
- `GET /places`, `/places/by-name`, `/places/nearby`, `/places/in-bounds`, `/places/{id}`
- `GET /categories`
- `GET/POST/PUT/PATCH/DELETE /point-of-interest/...`

### Versioned routes

The same routers are also mounted under `/api/v1`:

- `GET /api/v1/health`
- `GET /api/v1/places`
- etc.

New integrations should prefer `/api/v1` paths.

---

## Security and validation

### Regex escaping

Partial name and locality searches now escape user input:

```python
query["placeName"] = {"$regex": re.escape(name), "$options": "i"}
```

This prevents regex injection and ReDoS from malicious search strings.

### Geometry validation

`Geometry.coordinates` must be `[longitude, latitude]` with:

- Longitude: -180 to 180
- Latitude: -90 to 90

Invalid coordinates return HTTP 422 from Pydantic validation on create/update.

### POI ID allocation

On startup, a unique index is created on `demo_place_names.placeNameId`. Auto-generated IDs retry up to 3 times on `DuplicateKeyError`.

---

## Health check

`GET /health` now verifies database connectivity:

**200 OK**

```json
{"status": "ok", "database": "ok"}
```

**503 Service Unavailable** (MongoDB unreachable)

Response headers include `X-Request-ID` for tracing.

---

## Running locally

```powershell
cd GisApi
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI docs: http://127.0.0.1:8000/docs

---

## Running tests

```powershell
cd GisApi
pip install -r requirements-dev.txt
pytest
```

Tests use mocked MongoDB and repository dependency overrides — no live database required.

---

## Linting (optional)

```powershell
pip install ruff
ruff check app tests
ruff format app tests
```

---

## Breaking changes

**None for existing clients.** Response shapes and legacy URL paths are unchanged.

### Optional follow-ups (not implemented)

- Migrate GisPortal/GisAgent to `/api/v1` prefix only, then deprecate legacy paths
- Add MongoDB text index for full-text search instead of regex
- Integration tests against a test MongoDB container
- OpenAPI `examples` on every endpoint

---

## Files touched

| File | Action |
|------|--------|
| `app/config.py` | Rewritten with pydantic-settings |
| `app/database.py` | Lifespan helpers, index + ping |
| `app/dependencies.py` | **New** — DI and shared params |
| `app/exceptions.py` | **New** — global handlers |
| `app/logging_config.py` | **New** — request logging |
| `app/main.py` | CORS, lifespan, v1 routes, middleware |
| `app/models.py` | Re-exports from schemas |
| `app/schemas/*` | **New** — split models |
| `app/queries.py` | Regex escaping |
| `app/repositories/*` | Constructor injection, POI retry |
| `app/routers/*` | Depends(), OpenAPI summaries |
| `requirements.txt` | Pinned versions + test deps |
| `pyproject.toml` | **New** |
| `.env.example` | Added `CORS_ORIGINS`, `LOG_LEVEL` |
| `tests/*` | **New** |

---

## Review checklist

- [ ] Confirm `.env` has required variables after pulling changes
- [ ] Restart GisApi (`uvicorn main:app --reload`)
- [ ] Run `pytest` and confirm all tests pass
- [ ] Hit `GET /health` — expect `database: ok`
- [ ] Verify GisPortal name search still works (proxy to `/api` or direct URL)
- [ ] Verify GisAgent tool calls still resolve places
- [ ] Optionally set `CORS_ORIGINS` for production (not `*`)
