# paperjson

Paper-thin JSON serialization/deserialization for Python dataclasses. Easy to extend for custom classes.

## Usage

There are two ways to add `to_json()` / `from_json()` to a dataclass:

### 1A. Inherit from `SerdesBase`

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

This is similar to Pydantic BaseModel. But! You might not wish to add a base to your class.

### 1B. Use the `@serdes` decorator

Decorate any dataclass to inject the methods at runtime.  It works identically,
but type checkers can't see the injected methods:

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

You may choose both without conflict — inherit from `SerdesBase` and decorate with `@serdes`.

### 2. Type annotations with `SerdesProtocol`

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

## 3. Custom type support

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

### 4. Worked example

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


@paperjson.serdes
@dataclass
class User():
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
restored = User.from_json(json_str)
```

Output dataclasses are identical to those created:

```python
>>> print(restored)
User(name='Alice', dob=datetime.datetime(2026, 5, 19, 4, 50, 7, 485835, tzinfo=datetime.timezone.utc), email='alice@example.com', homedir=PosixPath('/home/tim'), mail=Address(line1='123 Main St', line2='', city='Springfield', st='IL', zip='62701'))
>>> obj == restored
True
```
