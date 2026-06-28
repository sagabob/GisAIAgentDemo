from enum import Enum


class SortBy(str, Enum):
    name = "name"
    ranking = "ranking"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"
