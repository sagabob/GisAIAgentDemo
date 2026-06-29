# GisAIAgentDemo

A demo GIS application centred on **GisPortal** — an Angular map UI for Christchurch place data. Users search by name or ask questions in plain English; results appear on an interactive Leaflet map with clickable pins.

**GisApi** (REST + MongoDB) and **GisAgent** (OpenAI tool-calling) exist to power the portal. The portal is the primary deliverable; the backends are supporting services.

---

## GisPortal — how it works

GisPortal answers one question: *“Help me find and explore Christchurch places on a map.”* It does that in two complementary ways.

### The screen

```
┌────────────────────────────────────────────────────┬─────────────────────┐
│  [ Search place name (min 3 chars) ]  12 results   │  Intelligent search │
│                                                    │  ─────────────────  │
│                                                    │  You: List beaches  │
│              LEAFLET MAP                             │  Agent: Found 25…   │
│         (OpenStreetMap tiles)                      │  ┌───────────────┐  │
│                                                    │  │ Sumner Beach  │  │
│    🔵 🔵 🔵  blue = result pins                    │  │ Taylor's Mistake│  │
│    🔴      red = selected place                    │  └───────────────┘  │
│                                                    │  [ Ask in English ] │
└────────────────────────────────────────────────────┴─────────────────────┘
```

- **Left / centre** — full-height map with a floating **name search** bar.
- **Right** — **intelligent search** chat panel (natural language).
- No top navigation bar; the map is the main canvas.

---

### Mode 1: Name search (direct API)

For users who know part of a place name and want fast, predictable results.

| Aspect | Behaviour |
|--------|-----------|
| **Trigger** | Type in the search overlay (no button) |
| **Minimum input** | 3 characters (configurable) |
| **Debounce** | 350 ms after typing stops |
| **Backend** | `GET /places?name=...` on **GisApi** |
| **Map** | All matches shown as **blue pins**; map zooms to fit |
| **Status** | “Searching…”, “N results”, or “Type to search” |

**Flow:**

1. Each keystroke (after trim) goes into an RxJS `Subject`.
2. Short queries clear markers and reset the status.
3. Valid queries call `GisApiService.searchPlaces()`.
4. `MapService.showPlaces()` drops invalid geometries, renders markers, and `fitBounds` (or zoom 15 for a single result).

Name search does **not** use the AI agent. It is a thin client over the GIS REST API — low latency, no OpenAI cost.

---

### Mode 2: Intelligent search (AI agent)

For exploratory questions: *“Show hospitals near the CBD”*, *“List all beaches”*, *“What parks are in Sumner?”*

| Aspect | Behaviour |
|--------|-----------|
| **Trigger** | Type in the sidebar textarea; **Enter** sends (Shift+Enter = new line) |
| **Backend** | `POST /chat` on **GisAgent** |
| **Agent** | OpenAI chooses tools → calls **GisApi** → returns structured data |
| **Chat UI** | Short summary + **clickable place list** (not long prose) |
| **Map** | Same blue pins as name search; clicking a list item **focuses** that place |
| **Session** | `session_id` kept for follow-up questions in the same conversation |
| **Reset** | Clears chat and agent memory |

**Why results are a list, not prose**

The agent could return numbered markdown lists with ratings and Google Maps links. That duplicates what the map already shows and is not clickable. The portal is designed to show:

1. One line of summary — e.g. `Found 25 places. Select one below to view on the map.`
2. A **button per place** (name, locality, rating)
3. Pins on the map for the same `places[]` array from the API response

Clicking a list item or a pin:

- Pans the map to that location (zoom ≥ 15)
- Turns the pin **red** (selected)
- Opens tooltip and popup (name, locality, category, rating, Google Maps link when available)

If a place in the list lacks coordinates, the portal fetches full details via `GET /places/{id}` and then focuses the map.

**Follow-up questions**

The portal sends the same `session_id` on each message so the agent remembers context — e.g. *“List beaches”* then *“Which ones are in Sumner?”* without re-explaining.

---

### Map behaviour (`MapService`)

All Leaflet logic lives in one injectable service; the UI component does not touch the map API directly.

| Method | Purpose |
|--------|---------|
| `attach(container)` | Create map centred on Christchurch CBD, OSM tiles |
| `showPlaces(places)` | Replace markers, fit bounds |
| `focusPlace(place)` | Red pin, pan, popup |
| `syncPlaces(places)` | Align markers with the current chat result set |
| `clearMarkers()` | Used when name search is cleared |
| `destroy()` | Cleanup on component destroy |

Coordinates are GeoJSON order **`[longitude, latitude]`** from the API; Leaflet expects `[lat, lng]` — conversion happens in `place.utils.ts`.

---

### Configuration

On startup the app loads **`/config.json`** before rendering (via `RuntimeConfigService`):

```json
{
  "gisApiUrl": "/api",
  "agentApiUrl": "/agent",
  "mapCenter": { "lat": -43.532, "lng": 172.636 },
  "defaultZoom": 12,
  "searchMinLength": 3,
  "searchDebounceMs": 350
}
```

| Environment | How config is set |
|-------------|-------------------|
| **Local dev** | `public/config.json` + `proxy.conf.json` (`/api` → GIS API, `/agent` → port 8001) |
| **Docker / Azure** | Container env vars → `docker-entrypoint.sh` writes `config.json` at start |

See [GisPortal/DEPLOY.md](./GisPortal/DEPLOY.md) for Azure Container Apps variables (`GIS_API_BASE_URL`, `AGENT_API_BASE_URL`, etc.).

---

### Portal code structure

```
GisPortal/src/app/
├── portal/                 # Main screen (template + orchestration)
├── services/
│   ├── gis-api.service.ts  # Name search + place-by-id fallback
│   ├── agent.service.ts    # Chat + reset
│   └── map.service.ts      # Leaflet map and markers
├── config/
│   └── runtime-config.service.ts
├── models/                 # Place, ChatMessage, ChatResponse
└── utils/
    ├── place.utils.ts      # Coordinates, summary text
    └── chat-message.formatter.ts  # Markdown for non-list agent replies
```

State in `PortalComponent` uses Angular **signals** (`chatMessages`, `searchLoading`, `aiLoading`, errors, `resultCount`).

More detail: [GisPortal/HOW_IT_WORKS.md](./GisPortal/HOW_IT_WORKS.md)

---

## Supporting services (behind the portal)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GisPortal (Angular + Leaflet)                  │
│   Name search ──────────────────────► GisApi                            │
│   Intelligent search (chat) ─────────► GisAgent ──tools──► GisApi       │
└─────────────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │    MongoDB      │
                                    │  place names    │
                                    └─────────────────┘
```

| Component | Tech | Port (local) | Role |
|-----------|------|--------------|------|
| **[GisPortal](./GisPortal/)** | Angular 21, Leaflet | 4200 / 8080 | **Primary UI** — map, search, chat |
| **[GisApi](./GisApi/)** | FastAPI, Motor | 8000 | Place data REST API |
| **[GisAgent](./GisAgent/)** | FastAPI, OpenAI | 8001 | Natural-language layer for chat |
| **GisDataMigration** | Python | — | Data load scripts |

---

## Repository layout

```
GisAIAgentDemo/
├── GisPortal/              # ★ Main application
│   ├── HOW_IT_WORKS.md
│   └── DEPLOY.md
├── GisApi/
├── GisAgent/
├── GisDataMigration/
├── .github/workflows/      # Docker Hub (manual trigger)
└── .env                    # Secrets (not committed)
```

---

## Quick start (local)

Run backends first, then the portal.

### 1. GisApi

```powershell
cd GisApi
pip install -r requirements-dev.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Set `MongoDB_URI` and `Target_DB_Name` in `GisApi/.env`.

### 2. GisAgent

```powershell
cd GisAgent
pip install -r requirements.txt
python -m uvicorn server:app --reload --host 127.0.0.1 --port 8001
```

Set `OPENAI_API_KEY` and `GIS_API_BASE_URL=http://127.0.0.1:8000` in `GisAgent/.env`.

### 3. GisPortal

```powershell
cd GisPortal
npm install
npm start
```

Open **http://localhost:4200**

- Name search uses `/api` proxy (edit `proxy.conf.json` target if needed).
- Intelligent search uses `/agent` proxy → localhost:8001.

---

## Example user journey

**Goal:** Find beaches and inspect one on the map.

1. User opens the portal — map loads centred on Christchurch.
2. In the right panel, user types *“List all beaches”* and presses Enter.
3. GisAgent queries GisApi; response includes `places[]` with geometries.
4. Sidebar shows `Found 25 places. Select one below to view on the map.` and a list of beaches.
5. Map shows 25 blue pins across the city.
6. User clicks **Sumner Beach** in the list → map pans to Sumner, pin turns red, popup shows rating and Google Maps link.
7. User asks *“Which of these have the highest ratings?”* — same session, agent uses conversation context.

---

## Docker & Azure

| Service | Container port | Notes |
|---------|----------------|-------|
| GisPortal | **8080** | nginx; set `GIS_API_BASE_URL` and `AGENT_API_BASE_URL` env vars |
| GisApi | 8000 | MongoDB connection required |
| GisAgent | 8000 | `OPENAI_API_KEY`, `GIS_API_BASE_URL` |

Configure **CORS** on Azure for GisApi and GisAgent so the browser (portal origin) can call them directly.

GitHub Actions: `docker-gis-portal.yml`, `docker-gis-api.yml`, `docker-gis-agent.yml` (manual `workflow_dispatch`). Requires `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, and image name variables.

---

## Tests

```powershell
cd GisApi && pytest
cd GisAgent && pip install -r requirements-dev.txt && pytest
cd GisPortal && npm test
```

---

## Documentation

| Document | Description |
|----------|-------------|
| **[GisPortal/HOW_IT_WORKS.md](./GisPortal/HOW_IT_WORKS.md)** | Portal architecture, flows, modules (detailed) |
| [GisPortal/DEPLOY.md](./GisPortal/DEPLOY.md) | Portal Docker & Azure |
| [GisAgent/HOW_IT_WORKS.md](./GisAgent/HOW_IT_WORKS.md) | Agent, tools, sessions |
| [GisApi/REFACTOR_REVIEW.md](./GisApi/REFACTOR_REVIEW.md) | REST API endpoints |

---

## License

Demo project — use and adapt as needed for your organisation.
