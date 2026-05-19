"""Unit tests for paperjson.deserialize — _DeserializerRegistry + register_deserializer."""

from datetime import datetime, timezone
from pathlib import Path

import paperjson
from paperjson.deserialize import _DeserializerRegistry, json_deserialize

# ---------------------------------------------------------------------------
# Registry mechanics
# ---------------------------------------------------------------------------


class TestDeserializerRegistry:
    """Low-level tests for _DeserializerRegistry."""

    def test_register_and_retrieve(self):
        reg = _DeserializerRegistry()

        @reg.register(int)
        def _(v: str) -> int:
            return int(v)

        assert reg.get(int) is not None
        fn = reg.get(int)
        assert fn("42") == 42

    def test_get_unregistered_returns_none(self):
        reg = _DeserializerRegistry()
        assert reg.get(str) is None

    def test_get_with_default(self):
        reg = _DeserializerRegistry()
        sentinel = object()
        assert reg.get(int, sentinel) is sentinel

    def test_contains(self):
        reg = _DeserializerRegistry()

        @reg.register(float)
        def _(v: str) -> float:
            return float(v)

        assert float in reg
        assert int not in reg

    def test_multiple_registrations(self):
        reg = _DeserializerRegistry()

        @reg.register(int)
        def int_handler(v: str) -> int:
            return int(v)

        @reg.register(float)
        def float_handler(v: str) -> float:
            return float(v)

        assert reg.get(int)("10") == 10
        assert reg.get(float)("3.14") == 3.14


# ---------------------------------------------------------------------------
# Built-in deserializers
# ---------------------------------------------------------------------------


class TestDatetimeDeserializer:
    """Built-in datetime deserializer: str → datetime."""

    def test_naive_iso_string(self):
        fn = json_deserialize.get(datetime)
        result = fn("2024-03-15T14:30:45")
        assert result == datetime(2024, 3, 15, 14, 30, 45)

    def test_utc_iso_string(self):
        fn = json_deserialize.get(datetime)
        result = fn("2024-03-15T14:30:45+00:00")
        assert result == datetime(2024, 3, 15, 14, 30, 45, tzinfo=timezone.utc)


class TestPathDeserializer:
    """Built-in Path deserializer: str → Path."""

    def test_absolute_path(self):
        fn = json_deserialize.get(Path)
        result = fn("/home/user/docs")
        assert result == Path("/home/user/docs")
        assert isinstance(result, Path)

    def test_relative_path(self):
        fn = json_deserialize.get(Path)
        result = fn("src/paperjson")
        assert result == Path("src/paperjson")


# ---------------------------------------------------------------------------
# Custom type registration (public API)
# ---------------------------------------------------------------------------


class TestRegisterDeserializer:
    """Register deserializers via the public paperjson.register_deserializer."""

    def test_register_custom_type(self):
        class Color:
            def __init__(self, r: int, g: int, b: int):
                self.r = r
                self.g = g
                self.b = b

            def __eq__(self, other):
                return (self.r, self.g, self.b) == (other.r, other.g, other.b)

        @paperjson.register_deserializer(Color)
        def _(v: str) -> Color:
            # expect "#ff8000"
            v = v.lstrip("#")
            return Color(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))

        fn = json_deserialize.get(Color)
        result = fn("#ff8000")
        assert result == Color(255, 128, 0)

    def test_registration_returns_decorator(self):
        """register_deserializer should return a callable (decorator)."""

        class CustomId:
            def __init__(self, val: str):
                self.val = val

        dec = paperjson.register_deserializer(CustomId)
        assert callable(dec)

        @dec
        def _(v: str) -> CustomId:
            return CustomId(v)

        result = json_deserialize.get(CustomId)("abc")
        assert isinstance(result, CustomId)
        assert result.val == "abc"
