import asyncio
import datetime

from aiobotocore.client import AioBaseClient
from litestar import Litestar, post
import aiohttp

from ref_server_communication import get_cities, City, get_raw_city_stats_from_ref_server
from s3_communication import create_bucket, get_s3_client, push_city_stats_to_s3


@post("/process-request")
async def collect_cities_data_to_s3(data: dict[str, str]) -> None:
    # TODO read on litestar input data validation and apply instead of dict[str, str], maybe Pydantic
    date = datetime.datetime.strptime(data["date"],
                                      "%Y-%m-%d").date()
    async with get_s3_client() as s3_client:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
            cities = await get_cities(session)
            create_s3_buckets_tasks = (asyncio.create_task(create_bucket(s3_client, country)) for country in
                                       set(city.country for city in cities))
            transfer_city_stats_tasks = (asyncio.create_task(_transfer_city_stats_to_s3(session, s3_client, city, date))
                                         for
                                         city in cities)
            await asyncio.gather(*create_s3_buckets_tasks, *transfer_city_stats_tasks)


async def _transfer_city_stats_to_s3(session: aiohttp.ClientSession, s3_client: AioBaseClient, city: City,
                                     date: datetime.date) -> None:
    raw_city_stats = await get_raw_city_stats_from_ref_server(city, date, session)
    await push_city_stats_to_s3(city, date, raw_city_stats, s3_client)


app = Litestar([collect_cities_data_to_s3])
