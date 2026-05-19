"""Type stub for paperjson.serdes."""

from typing import Any, Callable, Protocol, TypeVar, overload

_T = TypeVar("_T")

# ---------------------------------------------------------------------------
# Public base class — the type-safe path
# ---------------------------------------------------------------------------

class SerdesBase:
    """Base class that provides ``to_json()`` and ``from_json()``.

    Inherit from this class (in addition to ``@dataclass``) to get full
    type-checker / LSP support for the serdes methods::

        from dataclasses import dataclass
        from paperjson import SerdesBase

        @dataclass
        class User(SerdesBase):
            name: str

        obj = User(name="Alice")
        print(obj.to_json())          # LSP knows this method
        obj2 = User.from_json('...')   # LSP knows this classmethod
    """

    def to_json(self, *args: Any, **kwargs: Any) -> str: ...
    @classmethod
    def from_json(cls: type[_T], data: str | bytes | bytearray) -> _T: ...

# ---------------------------------------------------------------------------
# Protocol describing what the decorator adds
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

# ---------------------------------------------------------------------------
# Decorator overloads
# ---------------------------------------------------------------------------

@overload
def serdes(cls: _T, /) -> _T: ...
@overload
def serdes(*, strict: bool = ...) -> Callable[[_T], _T]: ...
