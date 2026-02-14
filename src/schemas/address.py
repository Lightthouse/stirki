from pydantic import BaseModel


class StreetOut(BaseModel):
    name: str
    slug: str
    houses: list[str]


class AddressesOut(BaseModel):
    streets: list[StreetOut]
