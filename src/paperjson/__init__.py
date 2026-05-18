"""paperjson — Paper-thin JSON serialization/deserialization for Python dataclasses."""

from paperjson.mixin import JsonSerDes
from paperjson.serialize import json_deserialize, json_serialize

__all__ = [
    "JsonSerDes",
    "json_deserialize",
    "json_serialize",
]

__version__ = "0.1.0"
