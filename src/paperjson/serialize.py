"""Serialization singledispatch and built-in handlers for paperjson."""

from datetime import datetime
from functools import singledispatch
from pathlib import Path
from typing import Callable, Type


@singledispatch
def json_serialize(arg):
    """Serialize *arg* for ``json.dumps(default=...)``.

    ``@serdes``-decorated classes call this internally during ``to_json()``.
    Register handlers with ``@paperjson.register_serializer(Type)``.
    """
    s = str(arg)
    typ = type(arg)

    # Test round-trip: can the value survive str() → constructor?
    # If yes, auto-register the str() handler so subsequent calls skip
    # this check entirely.
    try:
        reconstructed = typ(s)
        if reconstructed == arg:
            json_serialize.register(typ, str)
            return s
    except Exception:
        pass

    raise TypeError(
        "Object of type %s is not JSON serializable. "
        "Register a serializer with @paperjson.register_serializer(%s)"
        % (typ, typ.__name__)
    )


@json_serialize.register(datetime)
def _(arg: datetime) -> str:
    return arg.isoformat()


@json_serialize.register(Path)
def _(arg: Path) -> str:
    return str(arg)


def register_serializer(typ: Type) -> Callable:
    """Decorator to register a serialization function for *typ*.

    The function receives a value of *typ* and must return a JSON-compatible
    Python object (``str``, ``int``, ``float``, ``list``, ``dict``, etc.).

    Usage::

        import paperjson

        @paperjson.register_serializer(Path)
        def _(p: Path) -> str:
            return str(p)
    """
    return json_serialize.register(typ)
