#!/bin/sh
set -eu

CONFIG_PATH="/usr/share/nginx/html/config.json"

cat > "${CONFIG_PATH}" <<EOF
{
  "gisApiUrl": "${GIS_API_BASE_URL:-}",
  "agentApiUrl": "${AGENT_API_BASE_URL:-}",
  "mapCenter": {
    "lat": ${MAP_CENTER_LAT:--43.532},
    "lng": ${MAP_CENTER_LNG:-172.636}
  },
  "defaultZoom": ${DEFAULT_ZOOM:-12},
  "searchMinLength": ${SEARCH_MIN_LENGTH:-3},
  "searchDebounceMs": ${SEARCH_DEBOUNCE_MS:-350}
}
EOF

echo "Wrote runtime config to ${CONFIG_PATH}"
exec "$@"
