from fastapi import APIRouter

from src.addresses import STREETS, STREETS_SLUG, HOUSE_STREET_MAP
from src.schemas.address import AddressesOut, StreetOut

router = APIRouter()


@router.get("", response_model=AddressesOut)
async def get_addresses():
    streets = [
        StreetOut(
            name=name,
            slug=STREETS_SLUG[name],
            houses=HOUSE_STREET_MAP.get(name, []),
        )
        for name in STREETS
    ]
    return AddressesOut(streets=streets)
