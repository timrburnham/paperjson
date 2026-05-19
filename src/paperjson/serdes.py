"""paperjson.serdes — decorator that adds ``to_json()`` / ``from_json()`` to a dataclass."""

import dataclasses
import json
from types import UnionType
from typing import Any, Callable, Protocol, Type, TypeVar, Union, cast

from paperjson.deserialize import json_deserialize
from paperjson.serialize import json_serialize

_T = TypeVar("_T")

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_primary_type(typ: Type) -> Type:
    """Extract the first non-None type from ``Optional[T]`` / ``Union[T, ...]``."""
    origin = getattr(typ, "__origin__", None)
    if origin is Union or origin is UnionType:
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

    # 3. Fallback: try the type constructor directly (e.g. int("5"), Path("/tmp"))
    try:
        if not isinstance(value, typ):
            return typ(value)
    except (TypeError, ValueError):
        # typ is a parameterized generic (list[str], dict[str, int], …)
        # or the constructor rejected the value — keep the original
        pass

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
# Public base class (type-safe alternative to the decorator)
# ---------------------------------------------------------------------------


class SerdesProtocol(Protocol[_T]):
    """Protocol describing the serdes interface — ``to_json()`` and ``from_json()``.

    Use this for type-annotations when you want to accept any serdes-compatible
    object (whether it inherits from :class:`SerdesBase` or was decorated with
    ``@serdes``)::

        from paperjson import SerdesProtocol

        def dump(obj: SerdesProtocol[Any]) -> str:
            return obj.to_json()

        def load(cls: type[SerdesProtocol[_T]], data: str) -> _T:
            return cls.from_json(data)
    """

    def to_json(self, *args: Any, **kwargs: Any) -> str: ...

    @classmethod
    def from_json(cls: type[_T], data: str | bytes | bytearray) -> _T: ...


class SerdesBase:
    """Base class that provides ``to_json()`` and ``from_json()``.

    Inherit from this class (in addition to using ``@dataclass``) to get
    full type-checker / LSP support for ``to_json()`` and ``from_json()``::

        from dataclasses import dataclass
        from paperjson import SerdesBase

        @dataclass
        class User(SerdesBase):
            name: str

        obj  = User(name="Alice")
        json_str = obj.to_json()
        obj2 = User.from_json(json_str)

    You can also use the ``@paperjson.serdes`` decorator together with this
    base class — the decorator’s methods will shadow the inherited ones.
    """

    def to_json(self, **kwargs: Any) -> str:
        return json.dumps(
            dataclasses.asdict(cast(Any, self)),
            default=json_serialize,
            ensure_ascii=False,
            **kwargs,
        )

    @classmethod
    def from_json(cls, data: str | bytes | bytearray):
        raw = json.loads(data)
        return cls(**_coerce_dict(cls, raw))


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

    cls.to_json = SerdesBase.to_json
    cls.from_json = classmethod(SerdesBase.from_json.__func__)

    return cls
