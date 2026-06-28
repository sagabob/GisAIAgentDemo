from fastapi import APIRouter

from app.models import CategoryListResponse
from app.repositories.places import place_repository

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoryListResponse)
async def list_categories() -> CategoryListResponse:
    return CategoryListResponse(items=await place_repository.list_categories())
