import { GIS_API_BASE_URL } from './gis-api-url';
import { AGENT_API_BASE_URL } from './agent-api-url';

export const environment = {
  production: false,
  gisApiUrl: GIS_API_BASE_URL,
  agentApiUrl: AGENT_API_BASE_URL,
  mapCenter: { lat: -43.532, lng: 172.636 },
  defaultZoom: 12,
  searchMinLength: 3,
  searchDebounceMs: 350,
};
