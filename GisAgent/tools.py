from collections.abc import Callable
from typing import Any

from api_client import GisApiClient

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_place_categories",
            "description": "List all place categories available in the Christchurch place names catalog.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_places",
            "description": "Search Christchurch place names with optional filters and sorting. For list-all queries use category with limit=100.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Partial place name match."},
                    "category": {"type": "string", "description": "Category filter, e.g. park, school, hospital."},
                    "locality": {"type": "string", "description": "Locality/suburb filter."},
                    "sort_by": {"type": "string", "enum": ["name", "ranking"]},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"]},
                    "skip": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_places_by_name",
            "description": "Search places by place name. Use exact=true for an exact name match.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {"type": "string", "description": "Place name to search for."},
                    "exact": {"type": "boolean", "description": "Exact match when true."},
                    "category": {"type": "string"},
                    "locality": {"type": "string"},
                    "sort_by": {"type": "string", "enum": ["name", "ranking"]},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"]},
                    "skip": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["place_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_place",
            "description": "Get a single place by placeNameId.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name_id": {"type": "integer", "description": "Unique place name ID."},
                },
                "required": ["place_name_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_places_nearby",
            "description": "Find places within a radius in meters of a latitude/longitude point.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude of search center."},
                    "lng": {"type": "number", "description": "Longitude of search center."},
                    "radius": {"type": "number", "description": "Search radius in meters."},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "locality": {"type": "string"},
                    "skip": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["lat", "lng", "radius"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_places_in_bounds",
            "description": "Find places inside a bounding box defined by north, south, east, and west.",
            "parameters": {
                "type": "object",
                "properties": {
                    "north": {"type": "number"},
                    "south": {"type": "number"},
                    "east": {"type": "number"},
                    "west": {"type": "number"},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "locality": {"type": "string"},
                    "sort_by": {"type": "string", "enum": ["name", "ranking"]},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"]},
                    "skip": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["north", "south", "east", "west"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_points_of_interest",
            "description": "List or search demo points of interest (editable catalog).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "locality": {"type": "string"},
                    "sort_by": {"type": "string", "enum": ["name", "ranking"]},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"]},
                    "skip": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_poi_categories",
            "description": "List categories available in the demo point-of-interest catalog.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_poi_by_name",
            "description": "Search demo points of interest by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name": {"type": "string"},
                    "exact": {"type": "boolean"},
                    "category": {"type": "string"},
                    "locality": {"type": "string"},
                    "sort_by": {"type": "string", "enum": ["name", "ranking"]},
                    "sort_order": {"type": "string", "enum": ["asc", "desc"]},
                    "skip": {"type": "integer", "minimum": 0},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["place_name"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_point_of_interest",
            "description": "Get a single demo point of interest by placeNameId.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name_id": {"type": "integer"},
                },
                "required": ["place_name_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_point_of_interest",
            "description": "Create a new demo point of interest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "placeName": {"type": "string"},
                    "locality": {"type": "string"},
                    "category": {"type": "string"},
                    "placeNameId": {"type": "integer"},
                    "geometry": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["Point"]},
                            "coordinates": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "[longitude, latitude]",
                            },
                        },
                        "required": ["type", "coordinates"],
                    },
                },
                "required": ["placeName", "geometry"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_point_of_interest",
            "description": "Partially update a demo point of interest by placeNameId.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name_id": {"type": "integer"},
                    "placeName": {"type": "string"},
                    "locality": {"type": "string"},
                    "category": {"type": "string"},
                    "geometry": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["Point"]},
                            "coordinates": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 2,
                            },
                        },
                        "required": ["type", "coordinates"],
                    },
                },
                "required": ["place_name_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_point_of_interest",
            "description": "Delete a demo point of interest by placeNameId.",
            "parameters": {
                "type": "object",
                "properties": {
                    "place_name_id": {"type": "integer"},
                },
                "required": ["place_name_id"],
                "additionalProperties": False,
            },
        },
    },
]


def _update_point_of_interest(client: GisApiClient, arguments: dict[str, Any]) -> Any:
    payload = dict(arguments)
    place_name_id = payload.pop("place_name_id")
    return client.update_point_of_interest(place_name_id, payload)


ToolHandler = Callable[[GisApiClient, dict[str, Any]], Any]

TOOL_HANDLERS: dict[str, ToolHandler] = {
    "list_place_categories": lambda client, _: client.list_place_categories(),
    "search_places": lambda client, args: client.search_places(**args),
    "search_places_by_name": lambda client, args: client.search_places_by_name(**args),
    "get_place": lambda client, args: client.get_place(args["place_name_id"]),
    "search_places_nearby": lambda client, args: client.search_places_nearby(**args),
    "search_places_in_bounds": lambda client, args: client.search_places_in_bounds(**args),
    "list_points_of_interest": lambda client, args: client.list_points_of_interest(**args),
    "list_poi_categories": lambda client, _: client.list_poi_categories(),
    "search_poi_by_name": lambda client, args: client.search_poi_by_name(**args),
    "get_point_of_interest": lambda client, args: client.get_point_of_interest(args["place_name_id"]),
    "create_point_of_interest": lambda client, args: client.create_point_of_interest(args),
    "update_point_of_interest": _update_point_of_interest,
    "delete_point_of_interest": lambda client, args: client.delete_point_of_interest(args["place_name_id"]),
}


def execute_tool(client: GisApiClient, tool_name: str, arguments: dict[str, Any]) -> Any:
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        raise ValueError(f"Unknown tool: {tool_name}")
    return handler(client, arguments)
