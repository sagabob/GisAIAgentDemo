# GisPortal Refactor Review

Angular 21 portal: Leaflet map, name search, and intelligent search sidebar. Refactored for separation of concerns and proxy-aligned environment URLs.

---

## Summary of changes

| Area | Before | After |
|------|--------|-------|
| `portal.ts` | ~430 lines, map + chat + search | ~200 lines, delegates map to `MapService` |
| Map logic | Inline in component | `services/map.service.ts` |
| Place helpers | Duplicated in component | `utils/place.utils.ts` |
| Models | Chat + Place in one file | `place.model.ts` + `chat.model.ts` |
| Environment | Hardcoded `localhost:8001` | `/agent` and `/api` via proxy in dev |
| Subscriptions | Agent calls not always torn down | `takeUntilDestroyed` on HTTP subscriptions |
| Dead code | `isValidPlace` unused | Removed |

---

## Project structure

```
GisPortal/src/
├── app/
│   ├── portal/
│   │   ├── portal.ts          # UI orchestration
│   │   ├── portal.html
│   │   └── portal.css
│   ├── services/
│   │   ├── gis-api.service.ts # GIS REST client
│   │   ├── agent.service.ts   # GisAgent /chat client
│   │   └── map.service.ts     # Leaflet map + markers
│   ├── models/
│   │   ├── place.model.ts
│   │   └── chat.model.ts
│   └── utils/
│       ├── place.utils.ts
│       └── chat-message.formatter.ts
├── environments/
│   ├── gis-api-url.ts         # Edit for API base URL
│   ├── agent-api-url.ts       # Dev: /agent
│   ├── environment.ts
│   └── environment.prod.ts
└── proxy.conf.json            # Dev proxies /api and /agent
```

---

## Dev URLs (proxy)

| Path | Proxied to |
|------|------------|
| `/api` | GIS API (Azure or local) |
| `/agent` | `http://127.0.0.1:8001` (GisAgent) |

Run with **`npm start`** (not plain `ng serve`) so `proxy.conf.json` is applied.

---

## Production configuration

Before `ng build`:

1. **`gis-api-url.ts`** — set full GIS API URL (e.g. Azure Container Apps).
2. **`environment.prod.ts`** — set `PROD_AGENT_API_URL` to your GisAgent URL.

Configure CORS on Azure for both APIs (browser calls them directly in production).

---

## Component responsibilities

### `PortalComponent`

- Name search debounce pipeline (RxJS)
- Chat UI state (`chatMessages`, `aiLoading`, errors)
- Agent session ID
- Delegates map rendering to `MapService`

### `MapService`

- Leaflet init, tiles, markers
- `showPlaces`, `focusPlace`, `syncPlaces`, `clearMarkers`
- Selected pin (red) vs default (blue)

### `GisApiService` / `AgentService`

Thin `HttpClient` wrappers — no business logic.

---

## Running

```powershell
# Terminal 1 — GisAgent
cd GisAgent
uvicorn server:app --host 127.0.0.1 --port 8001

# Terminal 2 — Portal
cd GisPortal
npm start
```

---

## Tests

```powershell
cd GisPortal
npm test
```

Includes `place.utils.spec.ts` (Vitest).

---

## Review checklist

- [ ] `npm start` — name search via `/api` proxy
- [ ] Intelligent search via `/agent` proxy
- [ ] Click place in chat → map focuses pin
- [ ] Reset clears chat and agent session
- [ ] Update `gis-api-url.ts` + `PROD_AGENT_API_URL` before production deploy
