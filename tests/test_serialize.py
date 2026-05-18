"""Unit tests for paperjson.serialize — json_serialize + register_serializer."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import paperjson
from paperjson.serialize import json_serialize

# ---------------------------------------------------------------------------
# Built-in serializers
# ---------------------------------------------------------------------------


class TestDatetimeSerializer:
    """json_serialize should convert datetime → ISO-8601 string."""

    def test_naive_datetime(self):
        dt = datetime(2024, 3, 15, 14, 30, 45)
        result = json_serialize(dt)
        assert result == "2024-03-15T14:30:45"

    def test_utc_datetime(self):
        dt = datetime(2024, 3, 15, 14, 30, 45, tzinfo=timezone.utc)
        result = json_serialize(dt)
        assert result == "2024-03-15T14:30:45+00:00"

    def test_roundtrip_through_json_dumps(self):
        """The serializer should work as json.dumps(default=…)."""
        dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        payload = {"timestamp": dt}
        raw = json.dumps(payload, default=json_serialize, ensure_ascii=False)
        parsed = json.loads(raw)
        assert parsed["timestamp"] == "2024-06-01T12:00:00+00:00"


class TestPathSerializer:
    """json_serialize should convert Path → str."""

    def test_posix_path(self):
        p = Path("/home/user/docs")
        result = json_serialize(p)
        assert result == "/home/user/docs"

    def test_relative_path(self):
        p = Path("src/paperjson")
        result = json_serialize(p)
        assert result == "src/paperjson"

    def test_roundtrip_through_json_dumps(self):
        p = Path("/var/log")
        payload = {"logdir": p}
        raw = json.dumps(payload, default=json_serialize, ensure_ascii=False)
        parsed = json.loads(raw)
        assert parsed["logdir"] == "/var/log"


# ---------------------------------------------------------------------------
# Custom type registration
# ---------------------------------------------------------------------------


class TestRegisterSerializer:
    """Register and use a custom serializer."""

    def test_register_custom_type(self):
        # Use a simple custom class
        class Color:
            def __init__(self, r: int, g: int, b: int):
                self.r = r
                self.g = g
                self.b = b

            def __eq__(self, other):
                return (self.r, self.g, self.b) == (other.r, other.g, other.b)

        @paperjson.register_serializer(Color)
        def _(c: Color) -> str:
            return f"#{c.r:02x}{c.g:02x}{c.b:02x}"

        c = Color(255, 128, 0)
        result = json_serialize(c)
        assert result == "#ff8000"

    def test_serialize_unknown_type_raises(self):
        """Unregistered types should raise TypeError."""

        class Unregistered:
            pass

        with pytest.raises(TypeError, match="not JSON serializable"):
            json_serialize(Unregistered())


# ---------------------------------------------------------------------------
# Edge-cases
# ---------------------------------------------------------------------------


class TestJsonSerializeEdgeCases:
    """Corner-case behaviour."""

    def test_none_value(self):
        # json.dumps passes None through directly, but json_serialize
        # receives it and raises because NoneType is not registered.
        with pytest.raises(TypeError):
            json_serialize(None)

    def test_nested_json_dumps_with_datetime_list(self):
        """A list of datetimes should work via the default= path."""
        dts = [
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            datetime(2024, 6, 15, tzinfo=timezone.utc),
        ]
        raw = json.dumps(dts, default=json_serialize, ensure_ascii=False)
        parsed = json.loads(raw)
        assert parsed == ["2024-01-01T00:00:00+00:00", "2024-06-15T00:00:00+00:00"]
