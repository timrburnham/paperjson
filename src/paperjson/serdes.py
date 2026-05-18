"""paperjson.serdes — decorator that adds ``to_json()`` / ``from_json()`` to a dataclass."""

from __future__ import annotations

import dataclasses
import json
from typing import Any, Callable, Type, Union

from paperjson.deserialize import json_deserialize
from paperjson.serialize import json_serialize

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_primary_type(typ: Type) -> Type:
    """Extract the first non-None type from ``Optional[T]`` / ``Union[T, ...]``."""
    origin = getattr(typ, "__origin__", None)
    if origin is Union:
        for arg in getattr(typ, "__args__", ()):
            if arg is not type(None):
                return arg
    return typ


def _coerce_field(value: Any, target_type: Any) -> Any:
    """Coerce a single field value to *target_type* if possible.

    Returns the (possibly coerced) value.
    """
    if value is None:
        return value

    typ = _get_primary_type(target_type)

    # 1. Registered deserializer
    deserializer = json_deserialize.get(typ)
    if deserializer is not None and not isinstance(value, typ):
        return deserializer(value)

    # 2. Nested dataclass from dict
    if dataclasses.is_dataclass(typ) and isinstance(value, dict):
        coerced = _coerce_dict(typ, value)
        return typ(**coerced)

    return value


def _coerce_dict(cls: Type, data: dict) -> dict:
    """Walk *data* and coerce every field to the type declared on *cls*."""
    if not dataclasses.is_dataclass(cls):
        return dict(data)

    result = dict(data)
    for field in dataclasses.fields(cls):
        if field.name not in result:
            continue
        result[field.name] = _coerce_field(result[field.name], field.type)
    return result


# ---------------------------------------------------------------------------
# Methods injected onto the decorated class
# ---------------------------------------------------------------------------


def _to_json(self, *args, **kwargs) -> str:
    return json.dumps(
        dataclasses.asdict(self),
        default=json_serialize,
        ensure_ascii=False,
        *args,
        **kwargs,
    )


def _from_json(cls, data: str | bytes | bytearray):
    raw = json.loads(data)
    coerced = _coerce_dict(cls, raw)
    return cls(**coerced)


# ---------------------------------------------------------------------------
# Public decorator
# ---------------------------------------------------------------------------


def serdes(cls=None, /, *, strict: bool = False) -> Callable:
    """Decorator that adds ``to_json()`` and ``from_json()`` to a dataclass.

    Mutates *cls* in-place and returns it unchanged.

    Usage::

        import paperjson

        @paperjson.serdes
        @dataclass
        class User:
            name: str

        obj  = User(name="Alice")
        json_str = obj.to_json()
        obj2 = User.from_json(json_str)

    Parameters
    ----------
    strict:
        Reserved for future use — currently has no effect.
    """
    if cls is None:
        # Called with keyword arguments:  @serdes(strict=True)
        return lambda c: serdes(c, strict=strict)

    cls.to_json = _to_json
    cls.from_json = classmethod(_from_json)

    return cls
