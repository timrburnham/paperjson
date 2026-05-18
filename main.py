"""Example: using paperjson with dataclasses."""

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

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


if __name__ == "__main__":
    ad_dict = dict(
        line1="3824 Jarren Ct",
        line2="",
        city="Chattanooga",
        st="TN",
        zip="37415",
    )
    ad1 = Address("3824 Jarren Ct", "", "Chattanooga", "TN", "37415")
    ad2 = Address(**ad_dict)
    print(ad1 == ad2)

    obj1 = User(
        name="",
        dob=datetime.now(UTC),
        email="",
        homedir=Path.home(),
        mail=ad2,
    )
    print(obj1)

    json1 = obj1.to_json()
    print(json1)

    obj2 = User.from_json(json1)
    print(obj2)

    print(obj1 == obj2)
