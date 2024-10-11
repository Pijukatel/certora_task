import asyncio
import datetime
import json
import pytest
import aiohttp

from litestar.testing import AsyncTestClient

from app_server import app
from city_details_proccesing import create_city_stats_from_city_data, combine_stats
from ref_server_communication import get_cities
from conftest import generate_example_city_data, generate_example_cities, EXAMPLE_ID_1, EXAMPLE_ID_2, EXAMPLE_ID_3
from s3_communication import get_s3_client


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
        await client.post(f"/process-request?date={some_date}")

    async with get_s3_client() as s3_client:
        for city_id in expected_cities:
            resp = await s3_client.get_object(Bucket=expected_cities[city_id].country,
                                              Key=f"{some_date}/{expected_cities[city_id].name}")
            stats_in_s3 = json.loads(await resp["Body"].content.read())
            assert stats_in_s3 == expected_stats[city_id]


@pytest.mark.asyncio
async def test_get_country_stats(run_dummy_ref_server, run_dummy_moto):
    """Top level end-to-end test that first sends some post request to populate S3 and then sends country-stats.

    Data setup before calling /country-stats?from=2024-02-02&to2024-02-04:
    2024-02-01 - Out of range, excluded
    2024-02-02 - Start of range, included
    2024-02-03 - Missing data! Expecting empty stats.
    2024-02-04 - End of range, included
    2024-02-05 - Out of range, excluded

    All days have same data for simplicity of the test.
    Country 1 contains example_city1_data + example_city2_data
    Country 2 contains example_city3_data
    """
    # Arrange
    before_date = str(datetime.date(2024, 2, 1))
    start_date = str(datetime.date(2024, 2, 2))
    end_date = str(datetime.date(2024, 2, 4))
    after_date = str(datetime.date(2024, 2, 5))

    example_cities = generate_example_cities()
    example_data = generate_example_city_data(start_date)

    stats_1 = create_city_stats_from_city_data(example_data[EXAMPLE_ID_1])
    stats_2 = create_city_stats_from_city_data(example_data[EXAMPLE_ID_2])
    stats_3 = create_city_stats_from_city_data(example_data[EXAMPLE_ID_3])
    combined_stats_1_2 = combine_stats([stats_1, stats_2])

    date_stats_1_2 = {'bus_count': combined_stats_1_2.bus_count,
                      'passenger_count': combined_stats_1_2.passenger_count,
                      'exist_accident': combined_stats_1_2.exist_accident,
                      'average_delay_s': combined_stats_1_2.average_delay_s}
    date_stats_3 = {'bus_count': stats_3.bus_count,
                    'passenger_count': stats_3.passenger_count,
                    'exist_accident': stats_3.exist_accident,
                    'average_delay_s': stats_3.average_delay_s}
    empty_stats = {'bus_count': 0, 'passenger_count': 0, 'exist_accident': False, 'average_delay_s': 0}

    expected_result = {
        example_cities[EXAMPLE_ID_1].country: {
            start_date: date_stats_1_2,
            '2024-02-03': empty_stats,
            end_date: date_stats_1_2},
        example_cities[EXAMPLE_ID_3].country: {
            start_date: date_stats_3,
            '2024-02-03': empty_stats,
            end_date: date_stats_3}
    }

    # Act
    async with AsyncTestClient(app=app) as client:
        post_requests_tasks = [
            client.post(f"/process-request?date={before_date}"),
            client.post(f"/process-request?date={start_date}"),
            client.post(f"/process-request?date={end_date}"),
            client.post(f"/process-request?date={after_date}"),
        ]
        await asyncio.gather(*post_requests_tasks)

        response = await client.get(f"/country-stats?from={start_date}&to{end_date}")

    # Assert
    assert json.loads(response.content) == expected_result
