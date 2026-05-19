# paperjson

Paper-thin JSON serialization/deserialization for Python dataclasses.

## Usage

There are two ways to add `to_json()` / `from_json()` to a dataclass:

### 1. Inherit from `SerdesBase` (recommended)

Inheriting from `SerdesBase` gives full **type-checker / LSP support** — your
editor will know about `to_json()` and `from_json()`:

```python
from dataclasses import dataclass
import paperjson

@dataclass
class User(paperjson.SerdesBase):
    name: str
    email: str

user = User(name="Alice", email="alice@example.com")
print(user.to_json())                    # {"name": "Alice", "email": "alice@example.com"}

restored = User.from_json(user.to_json())
print(restored == user)                  # True
```

### 2. Use the `@serdes` decorator

The decorator injects the methods at runtime.  It works identically but type
checkers can't see the injected methods:

```python
from dataclasses import dataclass
import paperjson

@paperjson.serdes
@dataclass
class User:
    name: str
    email: str

user = User(name="Alice", email="alice@example.com")
print(user.to_json())                    # {"name": "Alice", "email": "alice@example.com"}
```

You can also combine both — inherit from `SerdesBase` **and** use `@serdes`.

### Type annotations with `SerdesProtocol`

Use `SerdesProtocol` in function signatures to accept anything that has
`to_json()` / `from_json()` — whether it inherits from `SerdesBase` or was
decorated:

```python
from typing import Any
import paperjson

def dump(obj: paperjson.SerdesProtocol[Any]) -> str:
    return obj.to_json(indent=2)

def load(cls: type[SerdesProtocol[Any]], data: str) -> Any:
    return cls.from_json(data)
```

### Full worked example

```python
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass

import paperjson


@dataclass
class Address(paperjson.SerdesBase):
    line1: str
    line2: str
    city: str
    st: str
    zip: str


@dataclass
class User(paperjson.SerdesBase):
    name: str
    dob: datetime
    email: str
    homedir: Path
    mail: Address


obj = User(
    name="Alice",
    dob=datetime.now(timezone.utc),
    email="alice@example.com",
    homedir=Path.home(),
    mail=Address("123 Main St", "", "Springfield", "IL", "62701"),
)

json_str = obj.to_json()
print(json_str)

restored = User.from_json(json_str)
print(restored)
```

## Custom type support

```python
from decimal import Decimal

import paperjson


@paperjson.register_serializer(Decimal)
def _(val: Decimal) -> str:
    return str(val)


@paperjson.register_deserializer(Decimal)
def _(val: str) -> Decimal:
    return Decimal(val)
```
