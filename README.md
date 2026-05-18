# paperjson

Paper-thin JSON serialization/deserialization for Python dataclasses.

## Usage

```python
from datetime import UTC, datetime
from pathlib import Path
from dataclasses import dataclass

from paperjson import JsonSerDes


@dataclass
class Address(JsonSerDes):
    line1: str
    line2: str
    city: str
    st: str
    zip: str


@dataclass
class User(JsonSerDes):
    name: str
    dob: datetime
    email: str
    homedir: Path
    mail: Address


obj = User(
    name="Alice",
    dob=datetime.now(UTC),
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
from paperjson import JsonSerDes

@JsonSerDes.register_serializer(Decimal)
def _(val: Decimal) -> str:
    return str(val)

@JsonSerDes.register_deserializer(Decimal)
def _(val: str) -> Decimal:
    return Decimal(val)
```
