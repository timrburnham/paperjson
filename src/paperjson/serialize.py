from datetime import datetime
from functools import singledispatch
from pathlib import Path

from paperjson._registry import _DeserializerRegistry


@singledispatch
def json_serialize(arg):
    """Default JSON serializer.

    Register type-specific handlers with @json_serialize.register(Type).
    """
    raise TypeError(f"Object of type {type(arg)} is not JSON serializable")


@json_serialize.register(datetime)
def _(arg: datetime) -> str:
    return arg.isoformat()


@json_serialize.register(Path)
def _(arg: Path) -> str:
    return str(arg)


json_deserialize = _DeserializerRegistry()


@json_deserialize.register(datetime)
def _(value: str) -> datetime:
    return datetime.fromisoformat(value)


@json_deserialize.register(Path)
def _(value: str) -> Path:
    return Path(value)
