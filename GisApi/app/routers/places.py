from fastapi import APIRouter, HTTPException, Query

from app.enums import SortBy, SortOrder
from app.models import Place, PlaceBoundsResponse, PlaceListResponse, PlaceNearbyResponse
from app.repositories.places import place_repository

router = APIRouter(prefix="/places", tags=["places"])


def _validate_bounds(*, north: float, south: float, east: float, west: float) -> None:
    if north < south:
        raise HTTPException(status_code=422, detail="north must be greater than or equal to south")
    if east < west:
        raise HTTPException(status_code=422, detail="east must be greater than or equal to west")


@router.get("", response_model=PlaceListResponse)
async def search_places(
    name: str | None = Query(default=None, description="Search by place name (partial match)"),
    category: str | None = Query(default=None, description="Filter by category"),
    locality: str | None = Query(default=None, description="Filter by locality"),
    sort_by: SortBy = Query(default=SortBy.name, description="Sort by place name or Google rating"),
    sort_order: SortOrder = Query(default=SortOrder.asc, description="Ascending or descending order"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PlaceListResponse:
    return await place_repository.search(
        name=name,
        category=category,
        locality=locality,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get("/by-name", response_model=PlaceListResponse)
async def search_by_place_name(
    place_name: str = Query(..., min_length=1, description="Search by place name"),
    exact: bool = Query(default=False, description="Exact name match when true, partial match when false"),
    locality: str | None = Query(default=None, description="Filter by locality"),
    category: str | None = Query(default=None, description="Filter by category"),
    sort_by: SortBy = Query(default=SortBy.name, description="Sort by place name or Google rating"),
    sort_order: SortOrder = Query(default=SortOrder.asc, description="Ascending or descending order"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PlaceListResponse:
    return await place_repository.search(
        name=place_name,
        category=category,
        locality=locality,
        exact_name=exact,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get("/nearby", response_model=PlaceNearbyResponse)
async def search_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitude of the search center"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude of the search center"),
    radius: float = Query(..., gt=0, le=50000, description="Search radius in meters"),
    name: str | None = Query(default=None, description="Search by place name (partial match)"),
    category: str | None = Query(default=None, description="Filter by category"),
    locality: str | None = Query(default=None, description="Filter by locality"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PlaceNearbyResponse:
    return await place_repository.nearby(
        lat=lat,
        lng=lng,
        radius_meters=radius,
        name=name,
        category=category,
        locality=locality,
        skip=skip,
        limit=limit,
    )


@router.get("/in-bounds", response_model=PlaceBoundsResponse)
async def search_in_bounds(
    north: float = Query(..., ge=-90, le=90, description="Northern latitude bound"),
    south: float = Query(..., ge=-90, le=90, description="Southern latitude bound"),
    east: float = Query(..., ge=-180, le=180, description="Eastern longitude bound"),
    west: float = Query(..., ge=-180, le=180, description="Western longitude bound"),
    name: str | None = Query(default=None, description="Search by place name (partial match)"),
    category: str | None = Query(default=None, description="Filter by category"),
    locality: str | None = Query(default=None, description="Filter by locality"),
    sort_by: SortBy = Query(default=SortBy.name, description="Sort by place name or Google rating"),
    sort_order: SortOrder = Query(default=SortOrder.asc, description="Ascending or descending order"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PlaceBoundsResponse:
    _validate_bounds(north=north, south=south, east=east, west=west)
    return await place_repository.in_bounds(
        north=north,
        south=south,
        east=east,
        west=west,
        name=name,
        category=category,
        locality=locality,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get("/{place_name_id}", response_model=Place)
async def get_place(place_name_id: int) -> Place:
    place = await place_repository.get_by_id(place_name_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place
