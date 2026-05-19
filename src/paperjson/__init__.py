"""paperjson — Paper-thin JSON serialization/deserialization for Python dataclasses."""

from paperjson.deserialize import register_deserializer
from paperjson.serdes import SerdesBase, SerdesProtocol, serdes
from paperjson.serialize import register_serializer

__all__ = [
    "SerdesBase",
    "SerdesProtocol",
    "register_deserializer",
    "register_serializer",
    "serdes",
]

__version__ = "0.1.0"
