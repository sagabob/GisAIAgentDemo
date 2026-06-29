from dataclasses import dataclass

from fastapi import Depends, Query
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from starlette.requests import Request

from app.config import Settings, get_settings
from app.enums import SortBy, SortOrder
from app.repositories.places import PlaceRepository
from app.repositories.pointofinterest import PointOfInterestRepository


def get_app_settings() -> Settings:
    return get_settings()


def get_mongo_client(request: Request) -> AsyncIOMotorClient:
    return request.app.state.mongo_client


def get_places_collection(request: Request) -> AsyncIOMotorCollection:
    settings: Settings = request.app.state.settings
    client: AsyncIOMotorClient = request.app.state.mongo_client
    return client[settings.db_name][settings.target_collection_name]


def get_poi_collection(request: Request) -> AsyncIOMotorCollection:
    settings: Settings = request.app.state.settings
    client: AsyncIOMotorClient = request.app.state.mongo_client
    return client[settings.db_name][settings.demo_collection_name]


def get_place_repository(
    collection: AsyncIOMotorCollection = Depends(get_places_collection),
) -> PlaceRepository:
    return PlaceRepository(collection)


def get_poi_repository(
    collection: AsyncIOMotorCollection = Depends(get_poi_collection),
) -> PointOfInterestRepository:
    return PointOfInterestRepository(collection)


@dataclass(frozen=True)
class PaginationParams:
    skip: int
    limit: int


def pagination_params(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)


@dataclass(frozen=True)
class SortParams:
    sort_by: SortBy
    sort_order: SortOrder


def sort_params(
    sort_by: SortBy = Query(default=SortBy.name, description="Sort by place name or Google rating"),
    sort_order: SortOrder = Query(default=SortOrder.asc, description="Ascending or descending order"),
) -> SortParams:
    return SortParams(sort_by=sort_by, sort_order=sort_order)


@dataclass(frozen=True)
class TextSearchFilters:
    name: str | None
    category: str | None
    locality: str | None


def text_search_filters(
    name: str | None = Query(default=None, description="Search by place name (partial match)"),
    category: str | None = Query(default=None, description="Filter by category"),
    locality: str | None = Query(default=None, description="Filter by locality"),
) -> TextSearchFilters:
    return TextSearchFilters(name=name, category=category, locality=locality)


@dataclass(frozen=True)
class NameSearchParams:
    place_name: str
    exact: bool
    locality: str | None
    category: str | None


def name_search_params(
    place_name: str = Query(..., min_length=1, description="Search by place name"),
    exact: bool = Query(default=False, description="Exact name match when true, partial match when false"),
    locality: str | None = Query(default=None, description="Filter by locality"),
    category: str | None = Query(default=None, description="Filter by category"),
) -> NameSearchParams:
    return NameSearchParams(
        place_name=place_name,
        exact=exact,
        locality=locality,
        category=category,
    )
