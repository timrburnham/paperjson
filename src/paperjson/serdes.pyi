"""Type stub for paperjson.serdes."""

from typing import Any, Callable, Protocol, TypeVar, overload

_T = TypeVar("_T")

# ---------------------------------------------------------------------------
# Protocol describing what the decorator adds
# ---------------------------------------------------------------------------

class _JsonSerDesProtocol(Protocol):
    """Protocol describing the methods injected by ``@serdes``.

    You can use this in type-annotations for functions that accept any
    ``@paperjson.serdes``-decorated class or instance::

        import paperjson

        def dump(obj: paperjson.serdes._JsonSerDesProtocol) -> str:
            return obj.to_json()
    """

    def to_json(self, *args: Any, **kwargs: Any) -> str: ...
    @classmethod
    def from_json(cls: type[_T], data: str | bytes | bytearray) -> _T: ...

# ---------------------------------------------------------------------------
# Decorator overloads
# ---------------------------------------------------------------------------

@overload
def serdes(cls: _T, /) -> _T: ...
@overload
def serdes(*, strict: bool = ...) -> Callable[[_T], _T]: ...
