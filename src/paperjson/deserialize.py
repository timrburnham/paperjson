"""Deserialization registry and built-in deserializers for paperjson."""

from datetime import datetime
from pathlib import Path
from typing import Callable, Type


class _DeserializerRegistry:
    """Registry for deserialization functions, keyed by target type.

    Provides a singledispatch-style register decorator, but dispatches
    on the target type rather than the value's runtime type.
    """

    def __init__(self) -> None:
        self._map: dict[Type, Callable] = {}

    def register(self, typ: Type) -> Callable:
        """Decorator to register a deserializer for *typ*."""

        def decorator(func: Callable) -> Callable:
            self._map[typ] = func
            return func

        return decorator

    def get(self, typ: Type, default=None):
        return self._map.get(typ, default)

    def __contains__(self, typ: Type) -> bool:
        return typ in self._map


json_deserialize = _DeserializerRegistry()


@json_deserialize.register(datetime)
def _(value: str) -> datetime:
    return datetime.fromisoformat(value)


@json_deserialize.register(Path)
def _(value: str) -> Path:
    return Path(value)


def register_deserializer(typ: Type) -> Callable:
    """Decorator to register a deserialization function for *typ*.

    Usage::

        import paperjson

        @paperjson.register_deserializer(Path)
        def _(v: str) -> Path:
            return Path(v)
    """
    return json_deserialize.register(typ)
