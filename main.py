"""Example: using paperjson with dataclasses."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

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


if __name__ == "__main__":
    ad1 = Address("3824 Jarren Ct", "", "Chattanooga", "TN", "37415")
    ad2 = Address(
        line1="3824 Jarren Ct",
        line2="",
        city="Chattanooga",
        st="TN",
        zip="37415",
    )
    print(ad1 == ad2)

    obj1 = User(
        name="Alice",
        dob=datetime.now(UTC),
        email="alice@example.com",
        homedir=Path.home(),
        mail=ad2,
    )
    print(obj1)

    json1 = obj1.to_json()  # type: ignore
    print(json1)

    obj2 = User.from_json(json1)  # type: ignore
    print(obj2)

    print(obj1 == obj2)
