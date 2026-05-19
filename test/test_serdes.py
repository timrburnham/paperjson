"""Unit tests for paperjson.serdes — the ``@serdes`` decorator and ``SerdesBase``.

Focuses on ``to_json()`` → ``from_json()`` roundtrip behaviour with
JSON strings and Python dataclasses.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pytest

import paperjson
from paperjson import SerdesBase, SerdesProtocol

# ============================================================================
# Basic roundtrip — primitive fields only
# ============================================================================


class TestPrimitiveRoundtrip:
    """Roundtrip dataclasses containing only JSON-native types."""

    @paperjson.serdes
    @dataclass
    class Point:
        x: int
        y: int

    @paperjson.serdes
    @dataclass
    class Book:
        title: str
        pages: int
        price: float
        in_stock: bool

    def test_int_fields_roundtrip(self):
        p = self.Point(10, 20)
        raw = p.to_json()
        p2 = self.Point.from_json(raw)
        assert p2 == p
        assert isinstance(raw, str)
        parsed = json.loads(raw)
        assert parsed == {"x": 10, "y": 20}

    def test_mixed_primitives_roundtrip(self):
        b = self.Book("Moby Dick", 635, 12.99, True)
        raw = b.to_json()
        b2 = self.Book.from_json(raw)
        assert b2 == b

    def test_from_json_string_input(self):
        raw = '{"title": "Dune", "pages": 412, "price": 9.99, "in_stock": false}'
        b = self.Book.from_json(raw)
        assert b.title == "Dune"
        assert b.pages == 412
        assert b.price == 9.99
        assert b.in_stock is False

    def test_from_json_bytes_input(self):
        raw = b'{"title": "Dune", "pages": 412, "price": 9.99, "in_stock": false}'
        b = self.Book.from_json(raw)
        assert b.title == "Dune"

    def test_from_json_bytearray_input(self):
        raw = bytearray(
            b'{"title": "Dune", "pages": 412, "price": 9.99, "in_stock": false}'
        )
        b = self.Book.from_json(raw)
        assert b.title == "Dune"

    def test_default_values(self):
        """Fields with defaults should survive roundtrip."""

        @paperjson.serdes
        @dataclass
        class Config:
            host: str = "localhost"
            port: int = 8080

        c1 = Config()
        c2 = Config.from_json(c1.to_json())
        assert c2 == c1

    def test_factory_defaults(self):
        """fields with default_factory should survive roundtrip."""

        @paperjson.serdes
        @dataclass
        class Shelf:
            books: list[str] = field(default_factory=list)

        s1 = Shelf(["Dune", "1984"])
        s2 = Shelf.from_json(s1.to_json())
        assert s2 == s1

        s3 = Shelf()
        s4 = Shelf.from_json(s3.to_json())
        assert s4 == s3


# ============================================================================
# Nested dataclasses
# ============================================================================


class TestNestedDataclasses:
    """Roundtrip with dataclass fields (composition)."""

    def test_nested_roundtrip(self):
        """Two-level nesting: Person → Address."""

        @paperjson.serdes
        @dataclass
        class Address:
            street: str
            city: str

        @paperjson.serdes
        @dataclass
        class Person:
            name: str
            address: Address

        addr = Address("123 Main", "Springfield")
        person = Person("Alice", addr)
        raw = person.to_json()
        person2 = Person.from_json(raw)
        assert person2 == person
        assert person2.address == addr
        assert isinstance(person2.address, Address)

    def test_nested_from_json_dict(self):
        """from_json should coerce nested dicts to dataclass instances."""

        @paperjson.serdes
        @dataclass
        class Address:
            street: str
            city: str

        @paperjson.serdes
        @dataclass
        class Person:
            name: str
            address: Address

        raw = '{"name": "Bob", "address": {"street": "456 Oak", "city": "Shelbyville"}}'
        person = Person.from_json(raw)
        assert person.name == "Bob"
        assert isinstance(person.address, Address)
        assert person.address.street == "456 Oak"
        assert person.address.city == "Shelbyville"

    def test_triple_nesting(self):
        """Three levels of nesting."""

        @paperjson.serdes
        @dataclass
        class Country:
            name: str

        @paperjson.serdes
        @dataclass
        class City:
            name: str
            country: Country

        @paperjson.serdes
        @dataclass
        class Venue:
            name: str
            city: City

        venue = Venue("Stadium", City("Paris", Country("France")))
        roundtripped = Venue.from_json(venue.to_json())
        assert roundtripped == venue


# ============================================================================
# Optional / Union fields
# ============================================================================


class TestOptionalFields:
    """Roundtrip with Optional[T] / Union[T, None] fields."""

    @paperjson.serdes
    @dataclass
    class Profile:
        name: str
        nickname: Optional[str] = None
        score: Optional[int] = None

    def test_optional_none_roundtrip(self):
        p = self.Profile("Alice")
        raw = p.to_json()
        p2 = self.Profile.from_json(raw)
        assert p2 == p
        assert p2.nickname is None
        assert p2.score is None

    def test_optional_present_roundtrip(self):
        p = self.Profile("Bob", "Bobby", 42)
        raw = p.to_json()
        p2 = self.Profile.from_json(raw)
        assert p2 == p

    def test_null_in_json(self):
        raw = '{"name": "Carol", "nickname": null, "score": null}'
        p = self.Profile.from_json(raw)
        assert p.name == "Carol"
        assert p.nickname is None
        assert p.score is None

    def test_partial_null_in_json(self):
        raw = '{"name": "Dan", "nickname": "Danny", "score": null}'
        p = self.Profile.from_json(raw)
        assert p.name == "Dan"
        assert p.nickname == "Danny"
        assert p.score is None


# ============================================================================
# Built-in special types (datetime, Path)
# ============================================================================


class TestSpecialTypes:
    """Roundtrip for types with built-in handlers."""

    @paperjson.serdes
    @dataclass
    class LogEntry:
        message: str
        timestamp: datetime

    @paperjson.serdes
    @dataclass
    class FsNode:
        name: str
        path: Path

    def test_datetime_roundtrip_naive(self):
        entry = self.LogEntry("startup", datetime(2024, 7, 4, 8, 30, 0))
        entry2 = self.LogEntry.from_json(entry.to_json())
        assert entry2 == entry

    def test_datetime_roundtrip_utc(self):
        entry = self.LogEntry(
            "startup", datetime(2024, 7, 4, 8, 30, 0, tzinfo=timezone.utc)
        )
        entry2 = self.LogEntry.from_json(entry.to_json())
        assert entry2 == entry

    def test_datetime_from_json_string(self):
        raw = '{"message": "error", "timestamp": "2024-11-01T22:15:00+00:00"}'
        entry = self.LogEntry.from_json(raw)
        assert entry.message == "error"
        assert entry.timestamp == datetime(2024, 11, 1, 22, 15, 0, tzinfo=timezone.utc)

    def test_path_roundtrip(self):
        node = self.FsNode("config", Path("/etc/app/config.yaml"))
        node2 = self.FsNode.from_json(node.to_json())
        assert node2 == node
        assert isinstance(node2.path, Path)

    def test_path_from_json_string(self):
        raw = '{"name": "data", "path": "/var/data"}'
        node = self.FsNode.from_json(raw)
        assert node.name == "data"
        assert node.path == Path("/var/data")


# ============================================================================
# Custom type registration (full roundtrip)
# ============================================================================


class TestCustomTypeRoundtrip:
    """Register serializers + deserializers for a custom type, then roundtrip."""

    def test_color_roundtrip(self):
        class Color:
            def __init__(self, r: int, g: int, b: int):
                self.r = r
                self.g = g
                self.b = b

            def __eq__(self, other):
                return (self.r, self.g, self.b) == (other.r, other.g, other.b)

            def __repr__(self):
                return f"Color({self.r}, {self.g}, {self.b})"

        @paperjson.register_serializer(Color)
        def _(c: Color) -> str:
            return f"#{c.r:02x}{c.g:02x}{c.b:02x}"

        @paperjson.register_deserializer(Color)
        def _(v: str) -> Color:
            v = v.lstrip("#")
            return Color(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))

        @paperjson.serdes
        @dataclass
        class Theme:
            name: str
            bg: Color
            fg: Color

        theme = Theme("ocean", Color(32, 64, 128), Color(255, 255, 255))
        raw = theme.to_json()
        theme2 = Theme.from_json(raw)
        assert theme2 == theme


# ============================================================================
# List / dict fields
# ============================================================================


class TestCollectionFields:
    """Roundtrip with list[T] and dict[K,V] fields."""

    @paperjson.serdes
    @dataclass
    class Playlist:
        name: str
        tracks: list[str]

    @paperjson.serdes
    @dataclass
    class Settings:
        name: str
        values: dict[str, Any]

    def test_list_of_strings(self):
        pl = self.Playlist("Favorites", ["Song A", "Song B", "Song C"])
        pl2 = self.Playlist.from_json(pl.to_json())
        assert pl2 == pl

    def test_empty_list(self):
        pl = self.Playlist("Empty", [])
        pl2 = self.Playlist.from_json(pl.to_json())
        assert pl2 == pl

    def test_dict_values(self):
        s = self.Settings("App", {"theme": "dark", "timeout": 30, "debug": True})
        s2 = self.Settings.from_json(s.to_json())
        assert s2 == s

    @pytest.mark.xfail(
        reason="library does not yet recurse into list[T] items during coercion"
    )
    def test_list_of_datetimes_from_json_coerces(self):
        """from_json should coerce list items back to datetime objects."""

        @paperjson.serdes
        @dataclass
        class Calendar:
            name: str
            events: list[datetime]

        raw = '{"name": "Work", "events": ["2024-01-01T00:00:00+00:00", "2024-06-15T00:00:00+00:00"]}'
        cal = Calendar.from_json(raw)
        assert cal.name == "Work"
        assert all(isinstance(e, datetime) for e in cal.events)
        assert cal.events[0] == datetime(2024, 1, 1, tzinfo=timezone.utc)

    @pytest.mark.xfail(
        reason="library does not yet recurse into list[T] items during coercion"
    )
    def test_list_of_paths_from_json_coerces(self):
        """from_json should coerce list items back to Path objects."""

        @paperjson.serdes
        @dataclass
        class Project:
            name: str
            files: list[Path]

        raw = '{"name": "myproj", "files": ["src/main.py", "tests/test_main.py"]}'
        proj = Project.from_json(raw)
        assert proj.name == "myproj"
        assert all(isinstance(p, Path) for p in proj.files)
        assert proj.files[0] == Path("src/main.py")


# ============================================================================
# Decorator variants
# ============================================================================


class TestDecoratorSyntax:
    """Both bare and parameterized decorator forms should work."""

    def test_bare_decorator(self):
        @paperjson.serdes
        @dataclass
        class A:
            x: int

        a = A(1)
        raw = a.to_json()
        parsed = json.loads(raw)
        assert parsed == {"x": 1}
        assert A.from_json(raw) == a

    def test_parameterized_decorator(self):
        @paperjson.serdes(strict=False)
        @dataclass
        class B:
            y: str

        b = B("hello")
        raw = b.to_json()
        parsed = json.loads(raw)
        assert parsed == {"y": "hello"}
        assert B.from_json(raw) == b

    def test_decorator_returns_same_class(self):
        """The decorator should return the same class, not a wrapper."""

        @paperjson.serdes
        @dataclass
        class C:
            z: float

        c = C(3.14)
        assert isinstance(c, C)
        assert type(c) is C


# ============================================================================
# Equality / non-equality after roundtrip
# ============================================================================


class TestEquality:
    """Dataclass equality should be preserved through roundtrip."""

    @paperjson.serdes
    @dataclass
    class Item:
        name: str
        quantity: int

    def test_equal_objects(self):
        a = self.Item("apple", 5)
        b = self.Item.from_json(a.to_json())
        assert a == b

    def test_different_objects(self):
        a = self.Item("apple", 5)
        b = self.Item("orange", 3)
        assert a != b


# ============================================================================
# to_json() extra args
# ============================================================================


class TestToJsonArgs:
    """``to_json()`` should pass extra kwargs through to ``json.dumps``."""

    @paperjson.serdes
    @dataclass
    class Entry:
        title: str

    def test_indent(self):
        e = self.Entry("Hello")
        raw = e.to_json(indent=2)
        assert "\n" in raw
        assert '  "title"' in raw or '  "' in raw  # indented

    def test_sort_keys(self):
        @paperjson.serdes
        @dataclass
        class Multi:
            b: int
            a: int
            c: int

        m = Multi(1, 2, 3)
        raw = m.to_json(sort_keys=True)
        parsed = json.loads(raw)
        keys = list(parsed.keys())
        assert keys == sorted(keys)


# ============================================================================
# Error cases
# ============================================================================


class TestErrorCases:
    """Things that should raise or fail gracefully."""

    def test_from_json_invalid_json(self):
        @paperjson.serdes
        @dataclass
        class Simple:
            x: int

        with pytest.raises(json.JSONDecodeError):
            Simple.from_json("not json")

    def test_from_json_wrong_type_passthrough(self):
        """Python dataclasses don't validate types at runtime — values pass through."""

        @paperjson.serdes
        @dataclass
        class Simple:
            x: int

        obj = Simple.from_json('{"x": "not an int"}')
        assert obj.x == "not an int"  # no coercion/validation for str->int


# ============================================================================
# SerdesBase — the type-safe base class
# ============================================================================


class TestSerdesBaseBasic:
    """Roundtrip via ``SerdesBase`` inheritance (no decorator)."""

    def test_primitive_roundtrip(self):
        @dataclass
        class Point(SerdesBase):
            x: int
            y: int

        p = Point(3, 4)
        raw = p.to_json()
        p2 = Point.from_json(raw)
        assert p2 == p
        assert json.loads(raw) == {"x": 3, "y": 4}

    def test_mixed_primitives(self):
        @dataclass
        class Book(SerdesBase):
            title: str
            pages: int
            price: float
            in_stock: bool

        b = Book("Dune", 412, 9.99, False)
        b2 = Book.from_json(b.to_json())
        assert b2 == b

    def test_isinstance_of_base(self):
        @dataclass
        class Item(SerdesBase):
            name: str

        i = Item("pen")
        assert isinstance(i, SerdesBase)
        assert isinstance(i, Item)

    def test_default_values(self):
        @dataclass
        class Config(SerdesBase):
            host: str = "localhost"
            port: int = 8080

        c1 = Config()
        c2 = Config.from_json(c1.to_json())
        assert c2 == c1

    def test_factory_defaults(self):
        @dataclass
        class Shelf(SerdesBase):
            books: list[str] = field(default_factory=list)

        s1 = Shelf(["Dune", "1984"])
        s2 = Shelf.from_json(s1.to_json())
        assert s2 == s1


class TestSerdesBaseNested:
    """Nested dataclasses via SerdesBase."""

    def test_two_level_nesting(self):
        @dataclass
        class Address(SerdesBase):
            street: str
            city: str

        @dataclass
        class Person(SerdesBase):
            name: str
            address: Address

        addr = Address("123 Main", "Springfield")
        person = Person("Alice", addr)
        person2 = Person.from_json(person.to_json())
        assert person2 == person
        assert isinstance(person2.address, Address)

    def test_nested_from_json_dict(self):
        @dataclass
        class Address(SerdesBase):
            street: str
            city: str

        @dataclass
        class Person(SerdesBase):
            name: str
            address: Address

        raw = '{"name": "Bob", "address": {"street": "456 Oak", "city": "Shelbyville"}}'
        person = Person.from_json(raw)
        assert isinstance(person.address, Address)
        assert person.address.street == "456 Oak"


class TestSerdesBaseOptional:
    """Optional / None fields with SerdesBase."""

    def test_optional_none_roundtrip(self):
        @dataclass
        class Profile(SerdesBase):
            name: str
            nickname: Optional[str] = None

        p = Profile("Alice")
        p2 = Profile.from_json(p.to_json())
        assert p2 == p
        assert p2.nickname is None

    def test_null_in_json(self):
        @dataclass
        class Profile(SerdesBase):
            name: str
            bio: Optional[str] = None

        raw = '{"name": "Carol", "bio": null}'
        p = Profile.from_json(raw)
        assert p.name == "Carol"
        assert p.bio is None


class TestSerdesBaseSpecialTypes:
    """datetime / Path roundtrip via SerdesBase."""

    def test_datetime_roundtrip(self):
        @dataclass
        class LogEntry(SerdesBase):
            message: str
            timestamp: datetime

        entry = LogEntry("startup", datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc))
        entry2 = LogEntry.from_json(entry.to_json())
        assert entry2 == entry

    def test_path_roundtrip(self):
        @dataclass
        class FsNode(SerdesBase):
            name: str
            path: Path

        node = FsNode("config", Path("/etc/app.yaml"))
        node2 = FsNode.from_json(node.to_json())
        assert node2 == node
        assert isinstance(node2.path, Path)


class TestSerdesBaseToJsonArgs:
    """Extra kwargs to to_json() work with SerdesBase."""

    def test_indent(self):
        @dataclass
        class Entry(SerdesBase):
            title: str

        e = Entry("Hello")
        raw = e.to_json(indent=2)
        assert "\n" in raw

    def test_sort_keys(self):
        @dataclass
        class Multi(SerdesBase):
            b: int
            a: int
            c: int

        m = Multi(1, 2, 3)
        raw = m.to_json(sort_keys=True)
        keys = list(json.loads(raw).keys())
        assert keys == sorted(keys)


class TestSerdesBaseBytesInput:
    """from_json accepts bytes and bytearray."""

    def test_from_bytes(self):
        @dataclass
        class Item(SerdesBase):
            name: str

        raw = b'{"name": "pen"}'
        i = Item.from_json(raw)
        assert i.name == "pen"

    def test_from_bytearray(self):
        @dataclass
        class Item(SerdesBase):
            name: str

        raw = bytearray(b'{"name": "pencil"}')
        i = Item.from_json(raw)
        assert i.name == "pencil"


# ============================================================================
# SerdesBase + @serdes decorator together
# ============================================================================


class TestSerdesBaseWithDecorator:
    """Using both ``SerdesBase`` inheritance and ``@serdes`` together."""

    def test_roundtrip(self):
        @paperjson.serdes
        @dataclass
        class Product(SerdesBase):
            name: str
            price: float

        p = Product("Widget", 19.99)
        p2 = Product.from_json(p.to_json())
        assert p2 == p

    def test_methods_still_accessible(self):
        @paperjson.serdes
        @dataclass
        class Item(SerdesBase):
            sku: str

        i = Item("ABC-123")
        assert hasattr(i, "to_json")
        assert callable(i.to_json)
        assert hasattr(Item, "from_json")
        assert callable(Item.from_json)

    def test_isinstance_of_both(self):
        @paperjson.serdes
        @dataclass
        class Widget(SerdesBase):
            name: str

        w = Widget("gizmo")
        assert isinstance(w, SerdesBase)
        assert isinstance(w, Widget)


# ============================================================================
# SerdesProtocol — the public Protocol type
# ============================================================================


class TestSerdesProtocol:
    """The ``SerdesProtocol`` type is importable and usable for annotations."""

    def test_importable_from_package(self):
        from paperjson import SerdesProtocol  # noqa: F811

        assert SerdesProtocol is not None

    def test_importable_from_serdes_module(self):
        from paperjson.serdes import SerdesProtocol

        assert SerdesProtocol is not None

    def test_serdes_base_instance_matches(self):
        """An instance of a SerdesBase subclass should have to_json/from_json."""

        @dataclass
        class Item(SerdesBase):
            name: str

        i = Item("test")
        assert hasattr(i, "to_json")
        assert hasattr(type(i), "from_json")

    def test_decorated_instance_matches(self):
        """An instance of a @serdes-decorated class should have to_json/from_json."""

        @paperjson.serdes
        @dataclass
        class Item:
            name: str

        i = Item("test")
        assert hasattr(i, "to_json")
        assert hasattr(type(i), "from_json")

    def test_structural_compatibility(self):
        """SerdesBase and @serdes instances expose the same protocol."""

        @dataclass
        class A(SerdesBase):
            x: int

        @paperjson.serdes
        @dataclass
        class B:
            x: int

        a = A(1)
        b = B(1)
        # Both have the same shape
        assert a.to_json() == b.to_json()
