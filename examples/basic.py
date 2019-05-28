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

import seperate_model_file

class City(Node):
    region: seperate_model_file.Region


if __name__ == "__main__":
    por = seperate_model_file.Region(name="Portugal")
    spa = seperate_model_file.Region(name="Spain")
    gas = seperate_model_file.Region(name="Gascony")
    mar = seperate_model_file.Region(name="Marseilles")

    mad = City(name="Madrid")

    por.borders = [spa]
    spa.borders = [por, gas, mar]
    gas.borders = [Facets(spa, foo="bar", hello="world"), mar]
    mar.borders = [spa, gas]

    mad.region = [spa]

    por.stage()
    spa.stage()
    gas.stage()
    mar.stage()

    mad.stage()

    print(generate_mutation())
    schema, unknown = Node._generate_schema()
    print(schema)
