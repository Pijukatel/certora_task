import datetime
import json

import pytest
import aiohttp

from litestar.testing import AsyncTestClient
from app_server import app
from city_details_proccesing import create_city_stats_from_city_data, create_stats_from_s3_metadata
from ref_server_communication import get_cities
from conftest import EXAMPLE_ID_1, generate_example_city_data, generate_example_cities

from s3_communication import get_s3_client, push_city_stats_to_s3, create_bucket


@pytest.mark.asyncio
async def test_get_cities(run_dummy_ref_server):
    """Tests that cities are correctly created from ref server response."""
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
        cities = await get_cities(session)
    expected_cities = set(generate_example_cities().values())
    assert cities == expected_cities


@pytest.mark.asyncio
async def test_process_request(run_dummy_ref_server, run_dummy_moto):
    """Tests that data is correctly transferred from ref server to S3."""
    some_date = str(datetime.date(2024, 2, 1))
    expected_cities = generate_example_cities()
    expected_stats = generate_example_city_data(some_date)
    async with AsyncTestClient(app=app) as client:
        await client.post("/process-request", content=json.dumps({"date": some_date}))

    async with get_s3_client() as s3_client:
        for city_id in expected_cities:
            resp = await s3_client.get_object(Bucket=expected_cities[city_id].country, Key=f"{some_date}/{expected_cities[city_id].name}")
            stats_in_s3 = json.loads(await resp["Body"].content.read())
            assert stats_in_s3 == expected_stats[city_id]


@pytest.mark.asyncio
async def test_data_pushed_to_s3_with_hash(run_dummy_moto):
    """Tests that data is correctly transferred from ref server to S3."""
    some_date = str(datetime.date(2024, 2, 1))
    example_city_data = generate_example_city_data(some_date)[EXAMPLE_ID_1]
    raw_city_stats = json.dumps(example_city_data).encode("utf-8")
    city = generate_example_cities()[EXAMPLE_ID_1]

    async with get_s3_client() as s3_client:
        await create_bucket(s3_client, city.country)
        await push_city_stats_to_s3(city, some_date, raw_city_stats, s3_client)

        metadata = await s3_client.head_object(Bucket=city.country, Key=f"{some_date}/{city.name}")
        assert create_stats_from_s3_metadata(metadata["Metadata"]) == create_city_stats_from_city_data(example_city_data)

