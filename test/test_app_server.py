import datetime
import json

import pytest
import aiohttp

from litestar.testing import AsyncTestClient
from app_server import app
from ref_server_communication import get_cities, City
from conftest import EXAMPLE_CITY_1, EXAMPLE_COUNTRY, EXAMPLE_ID_1, EXAMPLE_ID_2, EXAMPLE_CITY_2, \
    generate_example_city_data

from s3_communication import get_s3_client


@pytest.mark.asyncio
async def test_get_cities(run_dummy_ref_server):
    """Tests that cities are correctly created from ref server response."""
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        cities = await get_cities(session)
    expected_cities = {City(EXAMPLE_CITY_1, EXAMPLE_COUNTRY, EXAMPLE_ID_1),
                       City(EXAMPLE_CITY_2, EXAMPLE_COUNTRY, EXAMPLE_ID_2)}
    assert cities == expected_cities


@pytest.mark.asyncio
async def test_process_request(run_dummy_ref_server, run_dummy_moto):
    """Tests that data is correctly transferred from ref server to S3."""
    some_date = str(datetime.date(2024, 2, 1))
    expected_cities = {
        EXAMPLE_ID_1 : City(EXAMPLE_CITY_1, EXAMPLE_COUNTRY, EXAMPLE_ID_1),
        EXAMPLE_ID_2 : City(EXAMPLE_CITY_2, EXAMPLE_COUNTRY, EXAMPLE_ID_2)
    }
    expected_stats = generate_example_city_data(some_date)
    async with AsyncTestClient(app=app) as client:
        await client.post("/process-request", content=json.dumps({"date": some_date}))

    async with get_s3_client() as s3_client:
        for city_id in expected_cities:
            resp = await s3_client.get_object(Bucket=expected_cities[city_id].country, Key=f"{expected_cities[city_id].name}/{some_date}")
            stats_in_s3 = json.loads(await resp["Body"].content.read())
            assert stats_in_s3 == expected_stats[city_id]
