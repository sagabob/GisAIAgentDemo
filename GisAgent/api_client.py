from typing import Any

import httpx

from config import get_gis_api_base_url


class GisApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or get_gis_api_base_url()).rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        response = self._client.request(method, url, params=params, json=json_body)
        response.raise_for_status()
        if response.status_code == 204:
            return {"status": "deleted", "placeNameId": params.get("place_name_id") if params else None}
        return response.json()

    def get_health(self) -> dict[str, str]:
        return self.request("GET", "/health")

    def list_place_categories(self) -> dict[str, Any]:
        return self.request("GET", "/categories")

    def search_places(self, **params: Any) -> dict[str, Any]:
        return self.request("GET", "/places", params=_clean_params(params))

    def search_places_by_name(self, **params: Any) -> dict[str, Any]:
        return self.request("GET", "/places/by-name", params=_clean_params(params))

    def get_place(self, place_name_id: int) -> dict[str, Any]:
        return self.request("GET", f"/places/{place_name_id}")

    def search_places_nearby(self, **params: Any) -> dict[str, Any]:
        return self.request("GET", "/places/nearby", params=_clean_params(params))

    def search_places_in_bounds(self, **params: Any) -> dict[str, Any]:
        return self.request("GET", "/places/in-bounds", params=_clean_params(params))

    def list_points_of_interest(self, **params: Any) -> dict[str, Any]:
        return self.request("GET", "/point-of-interest", params=_clean_params(params))

    def list_poi_categories(self) -> dict[str, Any]:
        return self.request("GET", "/point-of-interest/categories")

    def search_poi_by_name(self, **params: Any) -> dict[str, Any]:
        return self.request("GET", "/point-of-interest/by-name", params=_clean_params(params))

    def get_point_of_interest(self, place_name_id: int) -> dict[str, Any]:
        return self.request("GET", f"/point-of-interest/{place_name_id}")

    def create_point_of_interest(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/point-of-interest", json_body=body)

    def replace_point_of_interest(self, place_name_id: int, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("PUT", f"/point-of-interest/{place_name_id}", json_body=body)

    def update_point_of_interest(self, place_name_id: int, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("PATCH", f"/point-of-interest/{place_name_id}", json_body=body)

    def delete_point_of_interest(self, place_name_id: int) -> dict[str, Any]:
        return self.request("DELETE", f"/point-of-interest/{place_name_id}")


def _clean_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if value is not None}
