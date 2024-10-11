import datetime
import json
import aiohttp
from litestar import Request
from logging import getLogger

from city_details_proccesing import City
from configuration import REFERENCE_SERVER

logger = getLogger(__name__)

async def get_cities(session: aiohttp.ClientSession) -> set[City]:
    async with session.get(f"{REFERENCE_SERVER}/cities") as response:
            response_text = await response.read()
            return set(City(city_dict["name"], city_dict["country"], city_dict["id"]) for city_dict in
                       json.loads(response_text))


async def get_raw_city_stats_from_ref_server(city: City, date: datetime.date, session: aiohttp.ClientSession) -> bytes:
    params = {"date": str(date)}
    async with session.get(f"{REFERENCE_SERVER}/cities/{city.id}/stats", params=params) as response:
        response_text = await response.read()
    return response_text


def parse_start_and_end_date_from_query_params(request: Request) -> tuple[datetime.date, datetime.date]:
    # TODO: There must be a better way. Find better way in Litestar documentation.
    query_params_names = set(request.query_params)
    query_params_names.remove("from")
    assert len(query_params_names) == 1
    malformed_date = query_params_names.pop()
    start_date = datetime.datetime.strptime(request.query_params.pop("from"), expected_date_format).date()
    end_date = datetime.datetime.strptime(malformed_date, "to" + expected_date_format).date()
    if end_date<start_date:
        logger.warning("End date must be larger than start date!")
    return start_date, end_date


expected_date_format = "%Y-%m-%d"
