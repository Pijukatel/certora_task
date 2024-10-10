import json
from dataclasses import dataclass

import aiohttp
from slugify import slugify

from configuration import REFERENCE_SERVER


@dataclass(unsafe_hash=True)
class City:
    name: str
    country: str
    id: int

    def __init__(self, name: str, country:str, id: int):
        self.name=slugify(name)
        self.country = slugify(country)
        self.id = id


async def get_cities(session: aiohttp.ClientSession) -> set[City]:
    async with session.get(f"{REFERENCE_SERVER}/cities") as response:
            response_text = await response.read()
            return set(City(city_dict["name"], city_dict["country"], city_dict["id"]) for city_dict in
                    json.loads(response_text))


async def get_raw_city_stats_from_ref_server(city, date, session) -> bytes:
    params = {"date": str(date)}
    async with session.get(f"{REFERENCE_SERVER}/cities/{city.id}/stats", params=params) as response:
        response_text = await response.read()
    return response_text
