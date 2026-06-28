from typing import Any

from pymongo import ReturnDocument

from app.config import get_poi_collection_name
from app.database import get_collection
from app.enums import SortBy, SortOrder
from app.models import (
    PointOfInterest,
    PointOfInterestCreate,
    PointOfInterestListResponse,
    PointOfInterestReplace,
    PointOfInterestUpdate,
)
from app.queries import build_filters, build_sort


def _serialize_poi(document: dict[str, Any]) -> PointOfInterest:
    payload = {key: value for key, value in document.items() if key != "_id"}
    return PointOfInterest.model_validate(payload)


class PointOfInterestRepository:
    def _collection(self):
        return get_collection(get_poi_collection_name())

    async def _next_place_name_id(self) -> int:
        document = await self._collection().find_one(
            {},
            sort=[("placeNameId", -1)],
            projection={"placeNameId": 1},
        )
        return (document["placeNameId"] + 1) if document else 1

    async def search(
        self,
        *,
        name: str | None = None,
        category: str | None = None,
        locality: str | None = None,
        exact_name: bool = False,
        sort_by: SortBy,
        sort_order: SortOrder,
        skip: int,
        limit: int,
    ) -> PointOfInterestListResponse:
        collection = self._collection()
        query = build_filters(
            name=name,
            category=category,
            locality=locality,
            exact_name=exact_name,
        )
        sort = build_sort(sort_by, sort_order)

        total = await collection.count_documents(query)
        cursor = collection.find(query, {"_id": 0}).sort(sort).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        items = [_serialize_poi(document) for document in documents]

        return PointOfInterestListResponse(
            total=total,
            skip=skip,
            limit=limit,
            sortBy=sort_by.value,
            sortOrder=sort_order.value,
            items=items,
        )

    async def get_by_id(self, place_name_id: int) -> PointOfInterest | None:
        document = await self._collection().find_one(
            {"placeNameId": place_name_id},
            {"_id": 0},
        )
        if not document:
            return None
        return _serialize_poi(document)

    async def create(self, payload: PointOfInterestCreate) -> PointOfInterest:
        collection = self._collection()
        place_name_id = payload.placeNameId
        if place_name_id is None:
            place_name_id = await self._next_place_name_id()
        elif await collection.find_one({"placeNameId": place_name_id}, {"_id": 1}):
            raise ValueError(f"placeNameId {place_name_id} already exists")

        document = {
            "placeNameId": place_name_id,
            "placeName": payload.placeName,
            "locality": payload.locality,
            "geometry": payload.geometry.model_dump(),
            "category": payload.category,
        }
        await collection.insert_one(document)
        return _serialize_poi(document)

    async def replace(self, place_name_id: int, payload: PointOfInterestReplace) -> PointOfInterest | None:
        document = {
            "placeNameId": place_name_id,
            "placeName": payload.placeName,
            "locality": payload.locality,
            "geometry": payload.geometry.model_dump(),
            "category": payload.category,
        }
        result = await self._collection().replace_one({"placeNameId": place_name_id}, document)
        if result.matched_count == 0:
            return None
        return _serialize_poi(document)

    async def update(self, place_name_id: int, payload: PointOfInterestUpdate) -> PointOfInterest | None:
        updates = payload.model_dump(exclude_unset=True)
        if "geometry" in updates and updates["geometry"] is not None:
            updates["geometry"] = payload.geometry.model_dump()

        if not updates:
            return await self.get_by_id(place_name_id)

        result = await self._collection().find_one_and_update(
            {"placeNameId": place_name_id},
            {"$set": updates},
            projection={"_id": 0},
            return_document=ReturnDocument.AFTER,
        )
        if not result:
            return None
        return _serialize_poi(result)

    async def delete(self, place_name_id: int) -> bool:
        result = await self._collection().delete_one({"placeNameId": place_name_id})
        return result.deleted_count > 0

    async def list_categories(self) -> list[str]:
        categories = await self._collection().distinct("category")
        return sorted(category for category in categories if category)


poi_repository = PointOfInterestRepository()
