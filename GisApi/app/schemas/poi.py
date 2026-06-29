from pydantic import BaseModel, ConfigDict

from app.schemas.common import Geometry


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
