import dataclasses
import json
from datetime import UTC, datetime
from functools import singledispatch
from pathlib import Path
from typing import Callable, Type, Union


class _DeserializerRegistry:
    """Registry for deserialization functions, keyed by target type.

    Provides a singledispatch-style register decorator, but dispatches
    on the target type rather than the value's runtime type.
    """

    def __init__(self):
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


class JsonSerDes:
    """Mixin class for JSON serialization/deserialization."""

    def __post_init__(self):
        for field in dataclasses.fields(self):  # type: ignore
            value = getattr(self, field.name)
            if value is None:
                continue

            # Get the first type from Optional/Union, skipping None
            target_type = self._get_primary_type(field.type)

            # Apply deserializer if we have one and value isn't already that type
            deserializer = json_deserialize.get(target_type)
            if deserializer is not None and not isinstance(value, target_type):
                coerced = deserializer(value)
                object.__setattr__(self, field.name, coerced)

    @staticmethod
    def _get_primary_type(typ):
        """Extract first not-None type from Optional[typ] or Union[typ, ...]."""
        origin = getattr(typ, "__origin__", None)
        if origin is Union:
            for arg in getattr(typ, "__args__", ()):
                if arg is not type(None):
                    return arg
        return typ

    @staticmethod
    def register_serializer(typ: Type) -> Callable:
        """Decorator to register a serialization function for a type.

        Delegates to singledispatch. Usage:
            @JsonSerDes.register_serializer(Path)
            def _(p: Path) -> str:
                return str(p)
        """
        return json_serialize.register(typ)

    @staticmethod
    def register_deserializer(typ: Type) -> Callable:
        """Decorator to register a deserialization function for a type.

        Usage:
            @JsonSerDes.register_deserializer(Path)
            def _(v: str) -> Path:
                return Path(v)
        """
        return json_deserialize.register(typ)

    def to_json(self, *args, **kwargs) -> str:
        return json.dumps(
            dataclasses.asdict(self),  # type: ignore
            default=json_serialize,
            ensure_ascii=False,
            *args,
            **kwargs,
        )

    @classmethod
    def from_json(cls, data: str | bytes | bytearray):
        json_data = json.loads(data)
        return cls(**json_data)


@dataclasses.dataclass
class Address(JsonSerDes):
    line1: str
    line2: str | None
    city: str
    st: str
    zip: str


@dataclasses.dataclass
class User(JsonSerDes):
    name: str
    dob: datetime
    email: str
    homedir: Path
    mail: Address


if __name__ == "__main__":
    ad = Address("3824 Jarren Ct", None, "Chattanooga", "TN", "37415")
    obj1 = User(name="", dob=datetime.now(UTC), email="", homedir=Path.home(), mail=ad)
    print(obj1)
    json1 = obj1.to_json()
    print(json1)
    obj2 = User.from_json(json1)
    print(obj2)
    print(obj1 == obj2)
