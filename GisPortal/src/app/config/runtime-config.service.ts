import { Injectable } from '@angular/core';

import { AppConfig } from './app-config.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class RuntimeConfigService {
  private config: AppConfig = {
    gisApiUrl: environment.gisApiUrl,
    agentApiUrl: environment.agentApiUrl,
    mapCenter: { ...environment.mapCenter },
    defaultZoom: environment.defaultZoom,
    searchMinLength: environment.searchMinLength,
    searchDebounceMs: environment.searchDebounceMs,
  };

  async load(): Promise<void> {
    try {
      const response = await fetch('/config.json', { cache: 'no-store' });
      if (!response.ok) {
        return;
      }

      const runtime = (await response.json()) as Partial<AppConfig>;
      this.config = {
        gisApiUrl: runtime.gisApiUrl ?? this.config.gisApiUrl,
        agentApiUrl: runtime.agentApiUrl ?? this.config.agentApiUrl,
        mapCenter: runtime.mapCenter ?? this.config.mapCenter,
        defaultZoom: runtime.defaultZoom ?? this.config.defaultZoom,
        searchMinLength: runtime.searchMinLength ?? this.config.searchMinLength,
        searchDebounceMs: runtime.searchDebounceMs ?? this.config.searchDebounceMs,
      };
    } catch {
      // Fall back to build-time environment defaults.
    }
  }

  get gisApiUrl(): string {
    return this.config.gisApiUrl;
  }

  get agentApiUrl(): string {
    return this.config.agentApiUrl;
  }

  get mapCenter(): { lat: number; lng: number } {
    return this.config.mapCenter;
  }

  get defaultZoom(): number {
    return this.config.defaultZoom;
  }

  get searchMinLength(): number {
    return this.config.searchMinLength;
  }

  get searchDebounceMs(): number {
    return this.config.searchDebounceMs;
  }
}
