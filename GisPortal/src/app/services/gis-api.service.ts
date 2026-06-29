import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { RuntimeConfigService } from '../config/runtime-config.service';
import { Place, PlaceListResponse } from '../models/place.model';

@Injectable({ providedIn: 'root' })
export class GisApiService {
  private readonly http = inject(HttpClient);
  private readonly config = inject(RuntimeConfigService);
  searchPlaces(
    query: string,
    options: { limit?: number; category?: string; locality?: string } = {},
  ): Observable<PlaceListResponse> {
    let params = new HttpParams()
      .set('name', query)
      .set('limit', String(options.limit ?? 50));

    if (options.category) {
      params = params.set('category', options.category);
    }
    if (options.locality) {
      params = params.set('locality', options.locality);
    }

    return this.http.get<PlaceListResponse>(`${this.config.gisApiUrl}/places`, { params });
  }

  getPlace(placeNameId: number): Observable<Place> {
    return this.http.get<Place>(`${this.config.gisApiUrl}/places/${placeNameId}`);  }
}
