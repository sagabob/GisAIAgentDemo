import { GIS_API_BASE_URL } from './gis-api-url';

/** Set agent URL here before production build, or override below. */
const PROD_AGENT_API_URL = 'https://YOUR_AGENT_API_URL';

export const environment = {
  production: true,
  gisApiUrl: GIS_API_BASE_URL,
  agentApiUrl: PROD_AGENT_API_URL,
  mapCenter: { lat: -43.532, lng: 172.636 },
  defaultZoom: 12,
  searchMinLength: 3,
  searchDebounceMs: 350,
};
