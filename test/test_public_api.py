"""Tests for the public API surface of ``paperjson``."""

import paperjson


class TestPublicApiExports:
    """Only the intended names should be exported."""

    def test_all_contains_expected(self):
        assert hasattr(paperjson, "__all__")
        expected = {"SerdesBase", "SerdesProtocol", "register_serializer", "register_deserializer", "serdes"}
        actual = set(paperjson.__all__)
        assert actual == expected

    def test_serdes_is_callable(self):
        assert callable(paperjson.serdes)

    def test_register_serializer_is_callable(self):
        assert callable(paperjson.register_serializer)

    def test_register_deserializer_is_callable(self):
        assert callable(paperjson.register_deserializer)

    def test_internal_names_not_exported(self):
        """json_serialize and json_deserialize should NOT be in __all__."""
        assert "json_serialize" not in paperjson.__all__
        assert "json_deserialize" not in paperjson.__all__

    def test_internal_modules_not_at_top_level(self):
        """Internal implementation details shouldn't leak to package level."""
        # _DeserializerRegistry should not be at package level
        assert not hasattr(paperjson, "_DeserializerRegistry")
        assert not hasattr(paperjson, "json_serialize")
        assert not hasattr(paperjson, "json_deserialize")


class TestVersion:
    """Package version string."""

    def test_version_is_string(self):
        assert isinstance(paperjson.__version__, str)
        assert paperjson.__version__ == "0.1.0"
