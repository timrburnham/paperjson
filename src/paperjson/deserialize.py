"""Deserialization registry and built-in handlers for paperjson."""

from datetime import datetime
from pathlib import Path
from typing import Callable, Type


class _DeserializerRegistry:
    """Thin registry for type-conditional deserialization functions.

    Works like :py:func:`functools.singledispatch` but dispatches on the
    *target* type (what you want back) rather than the runtime type of the
    argument (which is almost always ``str`` or ``dict``).
    """

    def __init__(self) -> None:
        self._map: dict[Type, Callable] = {}

    def register(self, typ: Type) -> Callable:
        """Register *func* as the deserializer for *typ*.

        Returns the decorator so it can be used with ``@register(typ)`` syntax.
        """

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

    The function receives a plain Python object (typically ``str``, ``list``,
    or ``dict``) and must return an instance of *typ*.

    Usage::

        import paperjson

        @paperjson.register_deserializer(Path)
        def _(v: str) -> Path:
            return Path(v)
    """
    return json_deserialize.register(typ)
