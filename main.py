import dataclasses
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, ClassVar, Type, Union


class _JsonSerDesMeta(type):
    """Metaclass for JsonSerDes that merges serializer registrations from parent classes."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Ensure _json_ser and _json_des exist on the class
        if not hasattr(cls, "_json_ser"):
            cls._json_ser = {}
        if not hasattr(cls, "_json_des"):
            cls._json_des = {}

        # Merge serializers from parent classes (child takes precedence)
        if hasattr(cls, "_json_ser"):
            merged_ser = {}
            for base in cls.__mro__:
                if base in (object, _JsonSerDesMeta):
                    continue
                base_ser = vars(base).get("_json_ser")
                if base_ser is not None:
                    # Merge in reverse MRO so child wins
                    for k, v in base_ser.items():
                        if k not in merged_ser:
                            merged_ser[k] = v
            cls._json_ser = merged_ser

        if hasattr(cls, "_json_des"):
            merged_des = {}
            for base in cls.__mro__:
                if base in (object, _JsonSerDesMeta):
                    continue
                base_des = vars(base).get("_json_des")
                if base_des is not None:
                    for k, v in base_des.items():
                        if k not in merged_des:
                            merged_des[k] = v
            cls._json_des = merged_des

        return cls


class JsonSerDes(metaclass=_JsonSerDesMeta):
    """Mixin class for JSON serialization/deserialization with inherited type registrations."""

    _json_ser: ClassVar[dict[Type, Callable]] = {
        datetime: lambda dt: dt.isoformat(),
        Path: lambda p: str(p),
    }
    _json_des: ClassVar[dict[Type, Callable]] = {
        datetime: lambda dt: datetime.fromisoformat(dt),
        Path: lambda p: Path(p),
    }

    def __post_init__(self):
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if value is None:
                continue

            # Get the first non-None type from Optional/Union
            target_type = self._get_primary_type(field.type)

            # Apply deserializer if we have one and value isn't already that type
            if target_type in self._json_des and not isinstance(value, target_type):
                coerced = self._json_des[target_type](value)
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
    def register_serializer(cls, typ=None):
        """Decorator to register a serialization function for a type.

        Usage:
            # With type argument:
            @JsonSerDes.register_serializer(Path)
            def serialize_path(p: Path) -> str:
                return str(p)

            # Without arguments (auto-detects return type):
            @JsonSerDes.register_serializer
            def serialize_path(p: Path) -> str:
                return str(p)
        """

        def decorator(func: Callable) -> Callable:
            target = typ

            # Auto-detect type from return annotation if not provided
            if target is None:
                hints = getattr(func, "__annotations__", {})
                if "return" in hints:
                    target = hints["return"]
                else:
                    raise ValueError(
                        "Type must be provided as argument or return annotation"
                    )

            cls._json_ser[target] = func
            return func

        # If called without arguments (@register_serializer), typ is the function
        if callable(typ) and not isinstance(typ, type):
            return decorator(typ)

        # If typ is a type, return decorator for immediate use
        if isinstance(typ, type):
            return decorator

        # Otherwise return decorator for later use
        return decorator

    def to_json(self, *args, **kwargs) -> str:
        def serialize(data: Any) -> Any:
            for T, func in reversed(self._json_ser.items()):
                if isinstance(data, T):
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
