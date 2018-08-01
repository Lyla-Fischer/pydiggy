from pydiggy.exceptions import ConflictingType, InvalidData
import inspect
import uuid
from itertools import count
from typing import get_type_hints, Union, List, _GenericAlias
from dataclasses import dataclass
from collections import namedtuple
from copy import deepcopy


DGRAPH_TYPES = {
    "str": "string",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "datetime": "dateTime",
}


def Facets(obj, **kwargs):
    f = namedtuple('Facets', ['obj'] + list(kwargs.keys()))
    return f(obj, *kwargs.values())


def is_facets(node):
    if isinstance(node, tuple) and hasattr(node, 'obj') and \
            node.__class__.__name__ == 'Facets':
        return True
    return False


@dataclass
class Node:
    uid: Union[uuid.UUID, int]

    _i = count()

    _nodes = []
    _staged = {}

    def __init_subclass__(cls, is_abstract: bool = False):
        if not is_abstract:
            cls._register_node(cls)

    def __init__(self, uid=None, **kwargs):
        if uid is None:
            uid = next(self._generate_uid())

        self.uid = uid

        for arg, val in kwargs.items():
            if arg in self.__annotations__:
                setattr(self, arg, val)

        # The following code looks to see if there are any typing.List
        # annotations. If yes, it auto creates an empty list.localns
        # This is probably not a feature worth including. Developer
        # should take responsibility for creating at run time.
        # localns = {x.__name__: x for x in Node._nodes}
        # localns.update({
        #     'List': List
        # })
        # annotations = get_type_hints(self, localns=localns)
        # for pred, pred_type in annotations.items():
        #     if isinstance(pred_type, _GenericAlias) and \
        #             pred_type.__origin__ == list:
        #         setattr(self, pred, [])

    def __repr__(self):
        return f'<{self.__class__.__name__}:{self.uid}>'

    @classmethod
    def _register_node(cls, node):
        cls._nodes.append(node)

    @classmethod
    def _get_name(cls):
        return cls.__name__

    @classmethod
    def _generate_schema(cls):
        nodes = cls._nodes
        edges = {}
        schema = []
        type_schema = []
        edge_schema = []
        unknown_schema = []

        type_schema.append(f"_type: string .")

        for node in nodes:
            name = node._get_name()
            type_schema.append(f"{name}: bool @index(bool) .")

            annotations = get_type_hints(node)
            for prop_name, prop_type in annotations.items():
                if prop_name in edges:
                    if prop_type != edges.get(
                        prop_name
                    ) and not cls._is_node_type(prop_type):
                        raise ConflictingType(
                            prop_name, prop_type, edges.get(prop_name)
                        )

                if isinstance(prop_type, _GenericAlias) and \
                        prop_type.__origin__ == list:
                    prop_type = prop_type.__args__[0]

                if prop_type in (str, int, bool):
                    edges[prop_name] = prop_type
                elif cls._is_node_type(prop_type):
                    edges[prop_name] = "uid"
                else:
                    if prop_name != 'uid':
                        unknown_schema.append(f"{prop_name}: {prop_type}")

        for edge_name, edge_type in edges.items():
            type_name = cls._get_type_name(edge_type)
            edge_schema.append(f"{edge_name}: {type_name} .")

        type_schema.sort()
        edge_schema.sort()

        schema = type_schema + edge_schema

        return "\n".join(schema), "\n".join(unknown_schema)

    @classmethod
    def _get_type_name(cls, schema_type):
        if isinstance(schema_type, str):
            return schema_type

        name = schema_type.__name__
        if cls._is_node_type(schema_type):
            return name
        else:
            if name not in DGRAPH_TYPES:
                raise Exception("Could not find type")
            return DGRAPH_TYPES.get(name)

    @classmethod
    def _get_staged(cls):
        return cls._staged

    @classmethod
    def _hydrate(cls, raw):
        registered = {x.__name__: x for x in Node._nodes}

        if '_type' in raw and raw.get('_type') in registered:
            if 'uid' not in raw:
                raise InvalidData('Missing uid.')

            keys = deepcopy(list(raw.keys()))
            facet_data = [
                (key.split('|')[1], raw.pop(key))
                for key in keys
                if '|' in key
            ]

            kwargs = {
                'uid': int(raw.pop('uid'), 16),
            }

            for pred, value in raw.items():

                if not pred.startswith('_') and pred in cls.__annotations__:
                    if isinstance(value, list):
                        value = [cls._hydrate(x) for x in value]
                    elif isinstance(value, dict):
                        value = cls._hydrate(value)
                    if value:
                        kwargs.update({pred: value})

            instance = cls(**kwargs)

            if facet_data:
                return Facets(instance, **dict(facet_data))
            else:
                return instance
        return None

    @staticmethod
    def _is_node_type(cls):
        """Check if a class is a <class 'Node'>"""
        return inspect.isclass(cls) and issubclass(cls, Node)

    def _generate_uid(self):
        i = next(self._i)
        yield f'unsaved.{i}'

    def stage(self):
        self.edges = {}

        for arg, _ in self.__annotations__.items():
            if not arg.startswith('_'):
                val = getattr(self, arg, None)
                if val:
                    self.edges[arg] = val
        self._staged[self.uid] = self

    def save(self):
        pass
