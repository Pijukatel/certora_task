import asyncio
import datetime
from collections import defaultdict
from logging import getLogger
from typing import Any

import aiohttp
from litestar import Litestar, MediaType, Request, get, post
from types_aiobotocore_s3 import S3Client

from city_details_proccesing import City
from ref_server_communication import (
    expected_date_format,
    get_cities,
    get_raw_city_stats_from_ref_server,
    parse_start_and_end_date_from_query_params,
)
from s3_communication import (
    create_bucket,
    get_aggregated_stats_for_country_and_date,
    get_s3_client,
    push_city_stats_to_s3,
)

logger = getLogger(__name__)

Result = dict[str, dict[str, Any]]


@post("/process-request")
async def collect_cities_data_to_s3(date: str) -> None:
    checked_date = datetime.datetime.strptime(date, expected_date_format).date()
    async with get_s3_client() as s3_client:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
            cities = await get_cities(session)
            create_s3_buckets_tasks = (
                asyncio.create_task(create_bucket(s3_client, country))
                for country in set(city.country for city in cities)
            )
            transfer_city_stats_tasks = (
                asyncio.create_task(
                    _transfer_city_stats_to_s3(session, s3_client, city, checked_date)
                )
                for city in cities
            )
            await asyncio.gather(*create_s3_buckets_tasks, *transfer_city_stats_tasks)


@get("/country-stats", media_type=MediaType.JSON)
async def get_country_stats(request: Request) -> Result:
    start_date, end_date = parse_start_and_end_date_from_query_params(request)
    dates = [
        str(start_date + datetime.timedelta(days=days))
        for days in range((end_date - start_date).days + 1)
    ]

    async with get_s3_client() as s3_client:
        countries = [
            bucket["Name"] for bucket in (await s3_client.list_buckets())["Buckets"]
        ]

        aggregate_stats_tasks = []
        for country in countries:
            for date in dates:
                aggregate_stats_tasks.append(
                    asyncio.create_task(
                        get_aggregated_stats_for_country_and_date(
                            country, date, s3_client
                        )
                    )
                )

        task_results = iter(await asyncio.gather(*aggregate_stats_tasks))

    # Fill result dict in same loop as gather keeps order of insertion.
    results: Result = defaultdict(dict)
    for country in countries:
        for date in dates:
            results[country][date] = next(task_results)
    return results


async def _transfer_city_stats_to_s3(
    session: aiohttp.ClientSession, s3_client: S3Client, city: City, date: datetime.date
) -> None:
    raw_city_stats = await get_raw_city_stats_from_ref_server(city, date, session)
    await push_city_stats_to_s3(city, date, raw_city_stats, s3_client)


app = Litestar([collect_cities_data_to_s3, get_country_stats], debug=False)
