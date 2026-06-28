from pydantic import BaseModel, ConfigDict


class Geometry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    coordinates: list[float]


class Ranking(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str | None = None
    rating: float | None = None
    reviewCount: int | None = None
    mapsUrl: str | None = None
    matchedName: str | None = None
    primaryType: str | None = None
    distanceMeters: float | None = None
    nameSimilarity: float | None = None


class Place(BaseModel):
    model_config = ConfigDict(extra="ignore")

    placeNameId: int
    placeName: str
    locality: str | None = None
    geometry: Geometry
    category: str | None = None
    categorySource: str | None = None
    categoryVerified: bool | None = None
    ranking: Ranking | None = None


class PlaceListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    sortBy: str
    sortOrder: str
    items: list[Place]


class PlaceSpatialItem(Place):
    distanceMeters: float | None = None


class PlaceNearbyResponse(BaseModel):
    total: int
    skip: int
    limit: int
    lat: float
    lng: float
    radiusMeters: float
    items: list[PlaceSpatialItem]


class PlaceBoundsResponse(BaseModel):
    total: int
    skip: int
    limit: int
    sortBy: str
    sortOrder: str
    north: float
    south: float
    east: float
    west: float
    items: list[Place]


class CategoryListResponse(BaseModel):
    items: list[str]


class PointOfInterest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    placeNameId: int
    placeName: str
    locality: str | None = None
    geometry: Geometry
    category: str | None = None


class PointOfInterestCreate(BaseModel):
    placeName: str
    locality: str | None = None
    geometry: Geometry
    category: str | None = None
    placeNameId: int | None = None


class PointOfInterestUpdate(BaseModel):
    placeName: str | None = None
    locality: str | None = None
    geometry: Geometry | None = None
    category: str | None = None


class PointOfInterestReplace(BaseModel):
    placeName: str
    locality: str | None = None
    geometry: Geometry
    category: str | None = None


class PointOfInterestListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    sortBy: str
    sortOrder: str
    items: list[PointOfInterest]
