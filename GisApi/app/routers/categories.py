from fastapi import APIRouter, Depends

from app.dependencies import get_place_repository
from app.repositories.places import PlaceRepository
from app.schemas.place import CategoryListResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse, summary="List place categories")
async def list_categories(
    repository: PlaceRepository = Depends(get_place_repository),
) -> CategoryListResponse:
    return CategoryListResponse(items=await repository.list_categories())
