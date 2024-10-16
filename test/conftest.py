import json
import time
from multiprocessing import Process
from typing import Any, cast

import aiohttp
import pytest
from aiohttp import web

from city_details_proccesing import City
from configuration import REFERENCE_SERVER_ADDRESS, REFERENCE_SERVER_PORT
from mocked_moto import mock_boto

EXAMPLE_CITY_1 = "City1"
EXAMPLE_ID_1 = 1
EXAMPLE_CITY_2 = "City 2"
EXAMPLE_ID_2 = 2
EXAMPLE_CITY_3 = "City 3"
EXAMPLE_ID_3 = 3
EXAMPLE_COUNTRY_1 = "Country1"
EXAMPLE_COUNTRY_2 = "Country2"


def generate_example_cities():
    return {
        EXAMPLE_ID_1: City(EXAMPLE_CITY_1, EXAMPLE_COUNTRY_1, EXAMPLE_ID_1),
        EXAMPLE_ID_2: City(EXAMPLE_CITY_2, EXAMPLE_COUNTRY_1, EXAMPLE_ID_2),
        EXAMPLE_ID_3: City(EXAMPLE_CITY_3, EXAMPLE_COUNTRY_2, EXAMPLE_ID_3),
    }


def generate_example_city_data(date: str) -> dict[int, list[dict[str, Any]]]:
    example_city1_data = [
        {
            "departure-time": f"{date}T05:25:00",
            "bus-type": "BUS-1",
            "passengers": 10,
            "delay": "PT100S",
            "accident": False,
        },
        {
            "departure-time": f"{date}T04:03:00",
            "bus-type": "BUS-2",
            "passengers": 20,
            "delay": "PT200S",
            "accident": True,
        },
    ]
    example_city2_data = [
        {
            "departure-time": f"{date}T05:25:00",
            "bus-type": "BUS-3",
            "passengers": 30,
            "delay": "PT300S",
            "accident": False,
        },
        {
            "departure-time": f"{date}T04:03:00",
            "bus-type": "BUS-4",
            "passengers": 40,
            "delay": "PT400S",
            "accident": False,
        },
    ]
    example_city3_data = [
        {
            "departure-time": f"{date}T05:25:00",
            "bus-type": "BUS-5",
            "passengers": 50,
            "delay": "PT500S",
            "accident": False,
        },
        {
            "departure-time": f"{date}T04:03:00",
            "bus-type": "BUS-6",
            "passengers": 60,
            "delay": "PT600S",
            "accident": False,
        },
    ]
    return {
        EXAMPLE_ID_1: example_city1_data,
        EXAMPLE_ID_2: example_city2_data,
        EXAMPLE_ID_3: example_city3_data,
    }


def example_cities_response():
    return [
        {"id": EXAMPLE_ID_1, "name": EXAMPLE_CITY_1, "country": EXAMPLE_COUNTRY_1},
        {"id": EXAMPLE_ID_2, "name": EXAMPLE_CITY_2, "country": EXAMPLE_COUNTRY_1},
        {"id": EXAMPLE_ID_3, "name": EXAMPLE_CITY_3, "country": EXAMPLE_COUNTRY_2},
    ]


def async_http_test_server():
    async def get_cities(request: aiohttp.web_request.Request):
        return web.Response(
            text=json.dumps(example_cities_response()), content_type="text/html"
        )

    async def get_city_stats(request: aiohttp.web_request.Request):
        city_id = cast(str, request.match_info.get("city_id"))
        date = request.rel_url.query["date"]
        example_city_data = generate_example_city_data(date)[int(city_id)]
        return web.Response(
            text=json.dumps(example_city_data), content_type="text/html"
        )

    app = web.Application()
    app.add_routes(
        [
            web.get("/cities", get_cities),
        ]
    )
    app.add_routes(
        [
            web.get("/cities/{city_id}/stats", get_city_stats),
        ]
    )
    web.run_app(app, host=REFERENCE_SERVER_ADDRESS, port=REFERENCE_SERVER_PORT)


@pytest.fixture(scope="session")
def run_dummy_ref_server():
    server_process = Process(target=async_http_test_server)
    server_process.start()
    time.sleep(1)
    yield
    server_process.kill()


@pytest.fixture(scope="function")
def run_dummy_moto():
    with mock_boto():
        yield
