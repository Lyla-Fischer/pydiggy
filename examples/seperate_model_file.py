from __future__ import annotations
from typing import List, Union

from pydiggy import (
    Facets,
    Node,
    count,
    generate_mutation,
    geo,
    index,
    lang,
    reverse,
    _types as types,
    upsert,
)

class Region(Node):

    from basic import City
    area: int = index(types._int)
    population: int = index
    description: str = lang
    short_description: str = lang()
    name: str = index(types.fulltext)
    abbr: str = (index(types.exact), count, upsert)
    coord: geo
    borders: List[Region] = reverse
    capitol: City

    # __upsert__ = area
    # __reverse__ = borders