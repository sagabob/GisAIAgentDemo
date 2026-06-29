import { Injectable, inject } from '@angular/core';
import * as L from 'leaflet';
import { Icon, Marker } from 'leaflet';

import { RuntimeConfigService } from '../config/runtime-config.service';
import { Place } from '../models/place.model';
import { getCoordinates, getPlaceId, normalizePlace } from '../utils/place.utils';

@Injectable({ providedIn: 'root' })
export class MapService {
  private readonly config = inject(RuntimeConfigService);
  private map?: L.Map;
  private markersLayer?: L.LayerGroup;
  private defaultIcon?: Icon;
  private selectedIcon?: Icon;
  private mapPlacesList: Place[] = [];
  private readonly markersById = new Map<number, L.Marker>();
  private selectedPlaceId: number | null = null;

  attach(container: HTMLElement): void {
    this.fixLeafletIcons();
    this.map = L.map(container, {
      center: [this.config.mapCenter.lat, this.config.mapCenter.lng],
      zoom: this.config.defaultZoom,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(this.map);

    this.markersLayer = L.layerGroup().addTo(this.map);
    setTimeout(() => this.map?.invalidateSize(), 0);
  }

  destroy(): void {
    this.map?.remove();
    this.map = undefined;
    this.markersLayer = undefined;
    this.markersById.clear();
    this.mapPlacesList = [];
    this.selectedPlaceId = null;
  }

  clearMarkers(): void {
    this.markersLayer?.clearLayers();
    this.markersById.clear();
    this.mapPlacesList = [];
    this.selectedPlaceId = null;
  }

  showPlaces(places: Place[]): boolean {
    if (!this.map || !this.markersLayer) {
      return false;
    }

    const validPlaces = places
      .map((place) => normalizePlace(place))
      .filter((place): place is Place => place !== null);

    if (validPlaces.length === 0) {
      return false;
    }

    this.mapPlacesList = validPlaces;
    this.selectedPlaceId = null;
    this.renderMapMarkers();
    this.map.invalidateSize();

    const bounds = validPlaces.map((place) => {
      const [lng, lat] = place.geometry.coordinates;
      return [lat, lng] as L.LatLngExpression;
    });

    if (bounds.length === 1) {
      this.map.setView(bounds[0], 15);
      return true;
    }

    this.map.fitBounds(L.latLngBounds(bounds), { padding: [40, 40] });
    return true;
  }

  syncPlaces(places: Place[]): void {
    const validPlaces = places
      .map((place) => normalizePlace(place))
      .filter((place): place is Place => place !== null);

    if (validPlaces.length === 0) {
      return;
    }

    this.mapPlacesList = validPlaces;
    this.renderMapMarkers();
  }

  focusPlace(place: Place): void {
    if (!this.map) {
      return;
    }

    const coords = getCoordinates(place);
    if (!coords) {
      return;
    }

    const placeKey = getPlaceId(place);
    if (!this.markersById.has(placeKey)) {
      this.mapPlacesList = [...this.mapPlacesList, place];
      this.renderMapMarkers();
    }

    this.selectedPlaceId = placeKey;
    this.updateMarkerIcons();
    this.closeAllMarkerOverlays();

    const marker = this.markersById.get(placeKey);
    if (!marker) {
      return;
    }

    const [lng, lat] = coords;
    this.map.invalidateSize();
    this.map.setView([lat, lng], Math.max(this.map.getZoom(), 15), { animate: true });

    window.setTimeout(() => {
      marker.openTooltip();
      marker.openPopup();
    }, 300);
  }

  isSelected(place: Place): boolean {
    return this.selectedPlaceId === getPlaceId(place);
  }

  private renderMapMarkers(): void {
    if (!this.map || !this.markersLayer || !this.defaultIcon || !this.selectedIcon) {
      return;
    }

    this.markersLayer.clearLayers();
    this.markersById.clear();

    for (const place of this.mapPlacesList) {
      const [lng, lat] = place.geometry.coordinates;
      const placeKey = getPlaceId(place);
      const icon = placeKey === this.selectedPlaceId ? this.selectedIcon : this.defaultIcon;
      const marker = L.marker([lat, lng], { icon })
        .bindPopup(this.buildPopup(place))
        .bindTooltip(place.placeName, { direction: 'top', offset: [0, -36], permanent: false });

      marker.on('click', () => this.focusPlace(place));
      marker.addTo(this.markersLayer);
      this.markersById.set(placeKey, marker);
    }
  }

  private updateMarkerIcons(): void {
    if (!this.defaultIcon || !this.selectedIcon) {
      return;
    }

    for (const [placeId, marker] of this.markersById) {
      marker.setIcon(placeId === this.selectedPlaceId ? this.selectedIcon : this.defaultIcon);
    }
  }

  private closeAllMarkerOverlays(): void {
    for (const marker of this.markersById.values()) {
      marker.closeTooltip();
      marker.closePopup();
    }
  }

  private fixLeafletIcons(): void {
    this.defaultIcon = new Icon({
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    });
    this.selectedIcon = new Icon({
      iconUrl:
        'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
      iconRetinaUrl:
        'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41],
    });
    Marker.prototype.options.icon = this.defaultIcon;
  }

  private buildPopup(place: Place): string {
    const rating = place.ranking?.rating;
    const ratingText = rating != null ? `<br>Rating: ${rating}` : '';
    const category = place.category ? `<br>Category: ${place.category}` : '';
    const locality = place.locality ? `<br>Locality: ${place.locality}` : '';
    const mapsUrl = place.ranking?.mapsUrl;
    const mapsText = mapsUrl
      ? `<br><a href="${mapsUrl}" target="_blank" rel="noopener">View on Google Maps</a>`
      : '';
    return `<strong>${place.placeName}</strong>${locality}${category}${ratingText}${mapsText}`;
  }
}
