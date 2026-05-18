# paperjson

Paper-thin JSON serialization/deserialization for Python dataclasses.

## Usage

```python
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass

import paperjson


@paperjson.serdes
@dataclass
class Address:
    line1: str
    line2: str
    city: str
    st: str
    zip: str


@paperjson.serdes
@dataclass
class User:
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
