# GisPortal — Docker & Azure Container Apps

GisPortal is a static Angular app served by **nginx**. API URLs and map settings are injected at **container startup** from environment variables (no rebuild per environment).

---

## How configuration works

```
Container starts
  → docker-entrypoint.sh writes /config.json from env vars
  → nginx serves the Angular app
  → RuntimeConfigService fetches /config.json before bootstrap
  → Services use gisApiUrl, agentApiUrl, etc.
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GIS_API_BASE_URL` | **Yes** | — | Full GisApi URL (e.g. `https://your-gis-api.azurecontainerapps.io`) |
| `AGENT_API_BASE_URL` | **Yes** | — | Full GisAgent URL (e.g. `https://your-gis-agent.azurecontainerapps.io`) |
| `MAP_CENTER_LAT` | No | `-43.532` | Map centre latitude |
| `MAP_CENTER_LNG` | No | `172.636` | Map centre longitude |
| `DEFAULT_ZOOM` | No | `12` | Initial map zoom |
| `SEARCH_MIN_LENGTH` | No | `3` | Min chars for name search |
| `SEARCH_DEBOUNCE_MS` | No | `350` | Name search debounce (ms) |

**Local dev** (`npm start`): uses `public/config.json` with `/api` and `/agent` proxies — no Docker required.

---

## Build and run locally

```powershell
cd GisPortal

docker build -t gis-portal .

docker run -p 8080:8080 `
  -e GIS_API_BASE_URL=https://tdp-place-api.happyrock-e7211d98.australiaeast.azurecontainerapps.io `
  -e AGENT_API_BASE_URL=http://host.docker.internal:8001 `
  gis-portal
```

Open http://localhost:8080

On Linux/macOS, use your host agent URL instead of `host.docker.internal` if needed.

---

## Azure Container Apps

### 1. Push image

Use the GitHub workflow (if configured) or:

```powershell
docker tag gis-portal youruser/gis-portal:latest
docker push youruser/gis-portal:latest
```

### 2. Create / update Container App

| Setting | Value |
|---------|--------|
| **Ingress** | Enabled, external |
| **Target port** | `8080` |
| **Transport** | HTTP |

### 3. Environment variables

In the Container App → **Containers** → **Environment variables**:

```
GIS_API_BASE_URL=https://tdp-place-api.happyrock-e7211d98.australiaeast.azurecontainerapps.io
AGENT_API_BASE_URL=https://your-gis-agent.azurecontainerapps.io
```

Optional map/search tuning:

```
MAP_CENTER_LAT=-43.532
MAP_CENTER_LNG=172.636
DEFAULT_ZOOM=12
```

### 4. Health probe

- **Path:** `/health`
- **Port:** `8080`

### 5. CORS

The browser calls GisApi and GisAgent **directly** using the URLs in `config.json`. Configure **CORS on Azure** for both APIs to allow your portal origin (the Container App FQDN).

GisAgent does not enable CORS in-app — Azure/APIM handles it.

---

## Verify runtime config

After deploy, open:

```
https://your-portal.azurecontainerapps.io/config.json
```

You should see the URLs you set in environment variables.

---

## Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build (Node → nginx) |
| `nginx.conf` | SPA routing, `/health`, no-cache `config.json` |
| `docker-entrypoint.sh` | Writes `config.json` from env vars |
| `public/config.json` | Local dev defaults (proxy paths) |
| `src/app/config/runtime-config.service.ts` | Loads config at startup |

---

## Troubleshooting

| Issue | Check |
|-------|--------|
| Blank map / API errors | `config.json` URLs correct and APIs reachable from browser |
| CORS errors | Allow portal origin on GisApi and GisAgent in Azure |
| 404 on refresh | nginx `try_files` — should be included in image |
| Stale config after env change | Restart revision (config written only at container start) |
