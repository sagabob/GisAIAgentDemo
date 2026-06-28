from app.database import get_collection
from app.enums import SortBy, SortOrder
from app.models import Place, PlaceListResponse
from app.queries import build_filters, build_sort, serialize_place


class PlaceRepository:
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
    ) -> PlaceListResponse:
        collection = get_collection()
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
        items = [serialize_place(document) for document in documents]

        return PlaceListResponse(
            total=total,
            skip=skip,
            limit=limit,
            sortBy=sort_by.value,
            sortOrder=sort_order.value,
            items=items,
        )

    async def get_by_id(self, place_name_id: int) -> Place | None:
        collection = get_collection()
        document = await collection.find_one({"placeNameId": place_name_id}, {"_id": 0})
        if not document:
            return None
        return serialize_place(document)

    async def list_categories(self) -> list[str]:
        collection = get_collection()
        categories = await collection.distinct("category")
        return sorted(category for category in categories if category)


place_repository = PlaceRepository()
