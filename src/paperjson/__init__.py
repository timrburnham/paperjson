"""paperjson — Paper-thin JSON serialization/deserialization for Python dataclasses."""

from paperjson.deserialize import json_deserialize, register_deserializer
from paperjson.serdes import serdes
from paperjson.serialize import json_serialize, register_serializer

__all__ = [
    "json_deserialize",
    "json_serialize",
    "register_deserializer",
    "register_serializer",
    "serdes",
]

__version__ = "0.1.0"
