from datetime import datetime
from functools import singledispatch
from pathlib import Path
from typing import Callable, Type

from paperjson._registry import _DeserializerRegistry

# ---------------------------------------------------------------------------
# Serializer (singledispatch-based)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Deserializer (registry-based)
# ---------------------------------------------------------------------------


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
