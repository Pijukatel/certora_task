import asyncio
import datetime
from typing import Any

from litestar import Litestar, get
import json
import aiohttp

# Deployment is out of scope of the task. Simple string constants to be used as configuration.
REFERENCE_SERVER_ADDRESS = "http://127.0.0.1:8000"


async def get_cities(session: aiohttp.ClientSession) -> list[dict[str, str | int]]:
    async with session.get(f"{REFERENCE_SERVER_ADDRESS}/cities") as response:
        response_text = await response.read()
        return json.loads(response_text)


async def get_city_stats(session: aiohttp.ClientSession, city_id: int) -> list[dict[str, Any]]:
    params = {"date": str(datetime.date.today())}
    async with session.get(f"{REFERENCE_SERVER_ADDRESS}/cities/{city_id}/stats", params=params) as response:
        response_text = await response.read()
        return json.loads(response_text)


async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        cities = await get_cities(session)
        get_details_tasks = [asyncio.create_task(get_city_stats(session, city["id"])) for city in cities]
        await asyncio.gather(*get_details_tasks)
    return get_details_tasks


# TODO learn something about S3
# TODO push to S3 as soon as we get data from ref server
# TODO process data

resp = asyncio.run(main())
