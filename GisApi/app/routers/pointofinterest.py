from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import (
    NameSearchParams,
    PaginationParams,
    SortParams,
    TextSearchFilters,
    get_poi_repository,
    name_search_params,
    pagination_params,
    sort_params,
    text_search_filters,
)
from app.repositories.pointofinterest import PointOfInterestRepository
from app.schemas.place import CategoryListResponse
from app.schemas.poi import (
    PointOfInterest,
    PointOfInterestCreate,
    PointOfInterestListResponse,
    PointOfInterestReplace,
    PointOfInterestUpdate,
)

router = APIRouter(prefix="/point-of-interest", tags=["point-of-interest"])


@router.get("", response_model=PointOfInterestListResponse, summary="List points of interest")
async def list_point_of_interest(
    filters: TextSearchFilters = Depends(text_search_filters),
    sorting: SortParams = Depends(sort_params),
    pagination: PaginationParams = Depends(pagination_params),
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> PointOfInterestListResponse:
    return await repository.search(
        name=filters.name,
        category=filters.category,
        locality=filters.locality,
        sort_by=sorting.sort_by,
        sort_order=sorting.sort_order,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/categories", response_model=CategoryListResponse, summary="List POI categories")
async def list_categories(
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> CategoryListResponse:
    items = await repository.list_categories()
    return CategoryListResponse(items=items)


@router.get("/by-name", response_model=PointOfInterestListResponse, summary="Search POI by name")
async def search_by_name(
    params: NameSearchParams = Depends(name_search_params),
    sorting: SortParams = Depends(sort_params),
    pagination: PaginationParams = Depends(pagination_params),
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> PointOfInterestListResponse:
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


@router.get("/{place_name_id}", response_model=PointOfInterest, summary="Get POI by ID")
async def get_point_of_interest(
    place_name_id: int,
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> PointOfInterest:
    poi = await repository.get_by_id(place_name_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return poi


@router.post(
    "",
    response_model=PointOfInterest,
    status_code=status.HTTP_201_CREATED,
    summary="Create a point of interest",
)
async def create_point_of_interest(
    payload: PointOfInterestCreate,
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> PointOfInterest:
    try:
        return await repository.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{place_name_id}", response_model=PointOfInterest, summary="Replace a point of interest")
async def replace_point_of_interest(
    place_name_id: int,
    payload: PointOfInterestReplace,
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> PointOfInterest:
    poi = await repository.replace(place_name_id, payload)
    if not poi:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return poi


@router.patch("/{place_name_id}", response_model=PointOfInterest, summary="Update a point of interest")
async def update_point_of_interest(
    place_name_id: int,
    payload: PointOfInterestUpdate,
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> PointOfInterest:
    poi = await repository.update(place_name_id, payload)
    if not poi:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return poi


@router.delete("/{place_name_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a POI")
async def delete_point_of_interest(
    place_name_id: int,
    repository: PointOfInterestRepository = Depends(get_poi_repository),
) -> Response:
    deleted = await repository.delete(place_name_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
