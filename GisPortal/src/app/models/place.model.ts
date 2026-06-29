export interface Geometry {
  type: string;
  coordinates: [number, number];
}

export interface Ranking {
  source?: string | null;
  rating?: number | null;
  reviewCount?: number | null;
  mapsUrl?: string | null;
}

export interface Place {
  placeNameId: number;
  placeName: string;
  locality?: string | null;
  geometry: Geometry;
  category?: string | null;
  distanceMeters?: number | null;
  ranking?: Ranking | null;
}

export interface PlaceListResponse {
  total: number;
  skip: number;
  limit: number;
  sortBy: string;
  sortOrder: string;
  items: Place[];
}
