from typing import Callable, Type


class _DeserializerRegistry:
    """Registry for deserialization functions, keyed by target type.

    Provides a singledispatch-style register decorator, but dispatches
    on the target type rather than the value's runtime type.
    """

    def __init__(self) -> None:
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
