import dataclasses
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Type, Union

# Module-level serializer/deserializer registries
_json_ser: dict[Type, Callable] = {
    datetime: lambda dt: dt.isoformat(),
    Path: lambda p: str(p),
}
_json_des: dict[Type, Callable] = {
    datetime: lambda dt: datetime.fromisoformat(dt),
    Path: lambda p: Path(p),
}


class JsonSerDes:
    """Mixin class for JSON serialization/deserialization."""

    def __post_init__(self):
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if value is None:
                continue

            # Get the first type from Optional/Union, skipping None
            target_type = self._get_primary_type(field.type)

            # Apply deserializer if we have one and value isn't already that type
            if target_type in _json_des and not isinstance(value, target_type):
                coerced = _json_des[target_type](value)
                object.__setattr__(self, field.name, coerced)

    @staticmethod
    def _get_primary_type(typ):
        """Extract first non-None type from Optional[T] or Union[T, ...]."""
        origin = getattr(typ, "__origin__", None)
        if origin is Union:
            for arg in getattr(typ, "__args__", ()):
                if arg is not type(None):
                    return arg
        return typ

    @classmethod
    def register_serializer(cls, typ: Type) -> Callable:
        """Decorator to register a serialization function for a type.

        Usage:
            @JsonSerDes.register_serializer(Path)
            def serialize_path(p: Path) -> str:
                return str(p)
        """

        def decorator(func: Callable) -> Callable:
            _json_ser[typ] = func
            return func

        return decorator

    def to_json(self, *args, **kwargs) -> str:
        def serialize(data: Any) -> Any:
            for typ, func in reversed(_json_ser.items()):
                if isinstance(data, typ):
                    return func(data)
            raise TypeError("Object of type %s is not JSON serializable" % type(data))

        return json.dumps(
            dataclasses.asdict(self),
            default=serialize,
            ensure_ascii=False,
            *args,
            **kwargs,
        )

    @classmethod
    def from_json(cls, data: str | bytes | bytearray):
        json_data = json.loads(data)
        return cls(**json_data)


@dataclasses.dataclass
class User(JsonSerDes):
    name: str
    dob: datetime
    email: str
    homedir: Path


if __name__ == "__main__":
    obj1 = User(name="", dob=datetime.now(UTC), email="", homedir=Path.home())
    print(obj1)
    json1 = obj1.to_json()
    print(json1)
    obj2 = User.from_json(json1)
    print(obj2)
    print(obj1 == obj2)
