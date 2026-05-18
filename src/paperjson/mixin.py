import dataclasses
import json
from typing import Callable, Type, Union

from paperjson.serialize import json_deserialize, json_serialize


class JsonSerDes:
    """Mixin class for JSON serialization/deserialization.

    Inherit from this class in your dataclass to gain ``to_json()`` and
    ``from_json()`` methods.  Custom type handling is supported via the
    ``register_serializer`` / ``register_deserializer`` static decorators.
    """

    def __post_init__(self) -> None:
        for field in dataclasses.fields(self):  # type: ignore
            value = getattr(self, field.name)
            if value is None:
                continue

            target_type = self._get_primary_type(field.type)

            # 1. Use registered deserializer if one exists
            deserializer = json_deserialize.get(target_type)
            if deserializer is not None and not isinstance(value, target_type):
                coerced = deserializer(value)
                object.__setattr__(self, field.name, coerced)

            # 2. Fallback: hydrate nested dataclasses from dict
            elif dataclasses.is_dataclass(target_type) and isinstance(value, dict):
                coerced = target_type(**value)
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
        """Decorator to register a serialization function for *typ*.

        Delegates to singledispatch.  Usage::

            @JsonSerDes.register_serializer(Path)
            def _(p: Path) -> str:
                return str(p)
        """
        return json_serialize.register(typ)

    @staticmethod
    def register_deserializer(typ: Type) -> Callable:
        """Decorator to register a deserialization function for *typ*.

        Usage::

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
