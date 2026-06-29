export interface AppConfig {
  gisApiUrl: string;
  agentApiUrl: string;
  mapCenter: { lat: number; lng: number };
  defaultZoom: number;
  searchMinLength: number;
  searchDebounceMs: number;
}
