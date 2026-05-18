"""Type stub for paperjson.serialize."""

from typing import Any, Callable, Type

# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------

def json_serialize(arg: Any, /) -> Any: ...
def register_serializer(typ: Type) -> Callable[[Callable], Callable]: ...

# ---------------------------------------------------------------------------
# Deserializer registry
# ---------------------------------------------------------------------------

class _DeserializerRegistry:
    def register(self, typ: Type) -> Callable[[Callable], Callable]: ...
    def get(self, typ: Type, default: Any = ...) -> Callable | None: ...
    def __contains__(self, typ: Type) -> bool: ...

json_deserialize: _DeserializerRegistry

def register_deserializer(typ: Type) -> Callable[[Callable], Callable]: ...
