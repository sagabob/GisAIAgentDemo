from fastapi import APIRouter, HTTPException, Query, Response, status

from app.enums import SortBy, SortOrder
from app.models import (
    CategoryListResponse,
    PointOfInterest,
    PointOfInterestCreate,
    PointOfInterestListResponse,
    PointOfInterestReplace,
    PointOfInterestUpdate,
)
from app.repositories.pointofinterest import poi_repository

router = APIRouter(prefix="/point-of-interest", tags=["point-of-interest"])


@router.get("", response_model=PointOfInterestListResponse)
async def list_point_of_interest(
    name: str | None = Query(default=None, description="Search by place name (partial match)"),
    category: str | None = Query(default=None, description="Filter by category"),
    locality: str | None = Query(default=None, description="Filter by locality"),
    sort_by: SortBy = Query(default=SortBy.name, description="Sort by place name or Google rating"),
    sort_order: SortOrder = Query(default=SortOrder.asc, description="Ascending or descending order"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PointOfInterestListResponse:
    return await poi_repository.search(
        name=name,
        category=category,
        locality=locality,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories() -> CategoryListResponse:
    items = await poi_repository.list_categories()
    return CategoryListResponse(items=items)


@router.get("/by-name", response_model=PointOfInterestListResponse)
async def search_by_name(
    place_name: str = Query(..., min_length=1, description="Search by place name"),
    exact: bool = Query(default=False, description="Exact name match when true, partial match when false"),
    locality: str | None = Query(default=None, description="Filter by locality"),
    category: str | None = Query(default=None, description="Filter by category"),
    sort_by: SortBy = Query(default=SortBy.name, description="Sort by place name or Google rating"),
    sort_order: SortOrder = Query(default=SortOrder.asc, description="Ascending or descending order"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> PointOfInterestListResponse:
    return await poi_repository.search(
        name=place_name,
        category=category,
        locality=locality,
        exact_name=exact,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@router.get("/{place_name_id}", response_model=PointOfInterest)
async def get_point_of_interest(place_name_id: int) -> PointOfInterest:
    poi = await poi_repository.get_by_id(place_name_id)
    if not poi:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return poi


@router.post("", response_model=PointOfInterest, status_code=status.HTTP_201_CREATED)
async def create_point_of_interest(payload: PointOfInterestCreate) -> PointOfInterest:
    try:
        return await poi_repository.create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{place_name_id}", response_model=PointOfInterest)
async def replace_point_of_interest(
    place_name_id: int,
    payload: PointOfInterestReplace,
) -> PointOfInterest:
    poi = await poi_repository.replace(place_name_id, payload)
    if not poi:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return poi


@router.patch("/{place_name_id}", response_model=PointOfInterest)
async def update_point_of_interest(
    place_name_id: int,
    payload: PointOfInterestUpdate,
) -> PointOfInterest:
    poi = await poi_repository.update(place_name_id, payload)
    if not poi:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return poi


@router.delete("/{place_name_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_point_of_interest(place_name_id: int) -> Response:
    deleted = await poi_repository.delete(place_name_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Point of interest not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
