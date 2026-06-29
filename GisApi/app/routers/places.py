from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import (
    NameSearchParams,
    PaginationParams,
    SortParams,
    TextSearchFilters,
    get_place_repository,
    name_search_params,
    pagination_params,
    sort_params,
    text_search_filters,
)
from app.repositories.places import PlaceRepository
from app.schemas.place import Place, PlaceBoundsResponse, PlaceListResponse, PlaceNearbyResponse

router = APIRouter(prefix="/places", tags=["places"])


def _validate_bounds(*, north: float, south: float, east: float, west: float) -> None:
    if north < south:
        raise HTTPException(status_code=422, detail="north must be greater than or equal to south")
    if east < west:
        raise HTTPException(status_code=422, detail="east must be greater than or equal to west")


@router.get(
    "",
    response_model=PlaceListResponse,
    summary="Search places",
    responses={200: {"description": "Paginated place search results"}},
)
async def search_places(
    filters: TextSearchFilters = Depends(text_search_filters),
    sorting: SortParams = Depends(sort_params),
    pagination: PaginationParams = Depends(pagination_params),
    repository: PlaceRepository = Depends(get_place_repository),
) -> PlaceListResponse:
    return await repository.search(
        name=filters.name,
        category=filters.category,
        locality=filters.locality,
        sort_by=sorting.sort_by,
        sort_order=sorting.sort_order,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/by-name", response_model=PlaceListResponse, summary="Search places by name")
async def search_by_place_name(
    params: NameSearchParams = Depends(name_search_params),
    sorting: SortParams = Depends(sort_params),
    pagination: PaginationParams = Depends(pagination_params),
    repository: PlaceRepository = Depends(get_place_repository),
) -> PlaceListResponse:
    return await repository.search(
        name=params.place_name,
        category=params.category,
        locality=params.locality,
        exact_name=params.exact,
        sort_by=sorting.sort_by,
        sort_order=sorting.sort_order,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/nearby", response_model=PlaceNearbyResponse, summary="Search places near a point")
async def search_nearby(
    lat: float = Query(..., ge=-90, le=90, description="Latitude of the search center"),
    lng: float = Query(..., ge=-180, le=180, description="Longitude of the search center"),
    radius: float = Query(..., gt=0, le=50000, description="Search radius in meters"),
    filters: TextSearchFilters = Depends(text_search_filters),
    pagination: PaginationParams = Depends(pagination_params),
    repository: PlaceRepository = Depends(get_place_repository),
) -> PlaceNearbyResponse:
    return await repository.nearby(
        lat=lat,
        lng=lng,
        radius_meters=radius,
        name=filters.name,
        category=filters.category,
        locality=filters.locality,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/in-bounds", response_model=PlaceBoundsResponse, summary="Search places inside bounds")
async def search_in_bounds(
    north: float = Query(..., ge=-90, le=90, description="Northern latitude bound"),
    south: float = Query(..., ge=-90, le=90, description="Southern latitude bound"),
    east: float = Query(..., ge=-180, le=180, description="Eastern longitude bound"),
    west: float = Query(..., ge=-180, le=180, description="Western longitude bound"),
    filters: TextSearchFilters = Depends(text_search_filters),
    sorting: SortParams = Depends(sort_params),
    pagination: PaginationParams = Depends(pagination_params),
    repository: PlaceRepository = Depends(get_place_repository),
) -> PlaceBoundsResponse:
    _validate_bounds(north=north, south=south, east=east, west=west)
    return await repository.in_bounds(
        north=north,
        south=south,
        east=east,
        west=west,
        name=filters.name,
        category=filters.category,
        locality=filters.locality,
        sort_by=sorting.sort_by,
        sort_order=sorting.sort_order,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{place_name_id}", response_model=Place, summary="Get place by ID")
async def get_place(
    place_name_id: int,
    repository: PlaceRepository = Depends(get_place_repository),
) -> Place:
    place = await repository.get_by_id(place_name_id)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")
    return place
