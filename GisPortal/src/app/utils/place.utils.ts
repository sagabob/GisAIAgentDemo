import { Place } from '../models/place.model';

export function getPlaceId(place: Place): number {
  return Number(place.placeNameId);
}

export function getCoordinates(place: Place): [number, number] | null {
  const raw = place.geometry?.coordinates;
  if (!raw || raw.length < 2) {
    return null;
  }

  const lng = Number(raw[0]);
  const lat = Number(raw[1]);
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) {
    return null;
  }

  return [lng, lat];
}

export function normalizePlace(place: Place): Place | null {
  const coords = getCoordinates(place);
  if (!coords) {
    return null;
  }

  return {
    ...place,
    placeNameId: getPlaceId(place),
    geometry: {
      type: place.geometry?.type ?? 'Point',
      coordinates: coords,
    },
  };
}

export function placesSummary(places: Place[], total?: number | null): string {
  const shown = places.length;
  const count = total ?? shown;
  if (shown === 0) {
    return 'No places found.';
  }
  if (shown < count) {
    return `Found ${count} places. Showing ${shown} - select one to view on the map.`;
  }
  if (shown === 1) {
    return 'Found 1 place. Select it below to view on the map.';
  }
  return `Found ${shown} places. Select one below to view on the map.`;
}
