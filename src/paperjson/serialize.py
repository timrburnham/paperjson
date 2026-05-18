"""Serialization (singledispatch) and built-in serializers for paperjson."""

from datetime import datetime
from functools import singledispatch
from pathlib import Path
from typing import Callable, Type


@singledispatch
def json_serialize(arg):
    """Default JSON serializer.

    Register type-specific handlers with
    ``@paperjson.register_serializer(Type)`` or
    ``@json_serialize.register(Type)``.
    """
    raise TypeError(f"Object of type {type(arg)} is not JSON serializable")


@json_serialize.register(datetime)
def _(arg: datetime) -> str:
    return arg.isoformat()


@json_serialize.register(Path)
def _(arg: Path) -> str:
    return str(arg)


def register_serializer(typ: Type) -> Callable:
    """Decorator to register a serialization function for *typ*.

    Usage::

        import paperjson

        @paperjson.register_serializer(Path)
        def _(p: Path) -> str:
            return str(p)
    """
    return json_serialize.register(typ)
