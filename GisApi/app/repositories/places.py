from app.database import get_collection
from app.enums import SortBy, SortOrder
from app.models import Place, PlaceBoundsResponse, PlaceListResponse, PlaceNearbyResponse, PlaceSpatialItem
from app.queries import build_bounds_geometry, build_filters, build_sort, merge_query, serialize_place


def _serialize_place_spatial(document: dict) -> PlaceSpatialItem:
    payload = {key: value for key, value in document.items() if key != "_id"}
    return PlaceSpatialItem.model_validate(payload)


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

    async def nearby(
        self,
        *,
        lat: float,
        lng: float,
        radius_meters: float,
        name: str | None = None,
        category: str | None = None,
        locality: str | None = None,
        skip: int,
        limit: int,
    ) -> PlaceNearbyResponse:
        collection = get_collection()
        filters = build_filters(name=name, category=category, locality=locality)

        geo_near: dict = {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lng, lat]},
                "distanceField": "distanceMeters",
                "maxDistance": radius_meters,
                "spherical": True,
            }
        }
        if filters:
            geo_near["$geoNear"]["query"] = filters

        documents = await collection.aggregate(
            [geo_near, {"$skip": skip}, {"$limit": limit}, {"$project": {"_id": 0}}]
        ).to_list(length=limit)
        count_result = await collection.aggregate([geo_near, {"$count": "total"}]).to_list(length=1)
        total = count_result[0]["total"] if count_result else 0
        items = [_serialize_place_spatial(document) for document in documents]

        return PlaceNearbyResponse(
            total=total,
            skip=skip,
            limit=limit,
            lat=lat,
            lng=lng,
            radiusMeters=radius_meters,
            items=items,
        )

    async def in_bounds(
        self,
        *,
        north: float,
        south: float,
        east: float,
        west: float,
        name: str | None = None,
        category: str | None = None,
        locality: str | None = None,
        sort_by: SortBy,
        sort_order: SortOrder,
        skip: int,
        limit: int,
    ) -> PlaceBoundsResponse:
        collection = get_collection()
        query = merge_query(
            build_filters(name=name, category=category, locality=locality),
            build_bounds_geometry(north=north, south=south, east=east, west=west),
        )
        sort = build_sort(sort_by, sort_order)

        total = await collection.count_documents(query)
        cursor = collection.find(query, {"_id": 0}).sort(sort).skip(skip).limit(limit)
        documents = await cursor.to_list(length=limit)
        items = [serialize_place(document) for document in documents]

        return PlaceBoundsResponse(
            total=total,
            skip=skip,
            limit=limit,
            sortBy=sort_by.value,
            sortOrder=sort_order.value,
            north=north,
            south=south,
            east=east,
            west=west,
            items=items,
        )


place_repository = PlaceRepository()
