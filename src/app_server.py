import asyncio
import contextlib
from dataclasses import dataclass
import datetime
import os
from typing import Any

from aiobotocore.client import AioBaseClient
from botocore.exceptions import WaiterError, ClientError
from litestar import Litestar, get
import json
import aiohttp
import boto3
from moto.core import set_initial_no_auth_action_count
from slugify import slugify
from aiobotocore.session import get_session

# Deployment is out of scope of the task. Simple string constants to be used as a configuration.
REFERENCE_SERVER_ADDRESS = "http://127.0.0.1:8000"
AWS_ACCESS_KEY_ID = "some_id"
AWS_SECRET_ACCESS_KEY = "some_key"
AWS_REGION_NAME = "us-west-2"


@dataclass
class City:
    name: str
    country: str
    id: int


async def get_cities(session: aiohttp.ClientSession) -> list[City]:
    async with session.get(f"{REFERENCE_SERVER_ADDRESS}/cities") as response:
        response_text = await response.read()
        return [City(slugify(city_dict["name"]), slugify(city_dict["country"]), city_dict["id"]) for city_dict in
                json.loads(response_text)]


async def get_city_stats(session: aiohttp.ClientSession, city_id: int) -> list[dict[str, Any]]:
    params = {"date": str(datetime.date.today())}
    async with session.get(f"{REFERENCE_SERVER_ADDRESS}/cities/{city_id}/stats", params=params) as response:
        response_text = await response.read()
        return json.loads(response_text)


bucket_creation_lock = asyncio.Lock()


async def transfer_city_stats_to_s3(session: aiohttp.ClientSession, s3_client: AioBaseClient, city: City) -> list[
    dict[str, Any]]:
    params = {"date": str(datetime.date.today())}
    async with session.get(f"{REFERENCE_SERVER_ADDRESS}/cities/{city.id}/stats", params=params) as response:
        response_text = await response.read()

    async with bucket_creation_lock:
        try:
            await s3_client.get_waiter('bucket_exists').wait(Bucket=city.country,
                                                             WaiterConfig={"MaxAttempts": 1})
        except WaiterError:
            await s3_client.create_bucket(Bucket=city.country,
                                          CreateBucketConfiguration={"LocationConstraint": AWS_REGION_NAME})

    await s3_client.put_object(Bucket=city.country, Key=f"{city.name}", Body=response_text,
                               ContentType='application/json')

    # getting s3 object back
    # resp = await s3_client.get_object(Bucket=city.country, Key=f"{city.name}")
    # print(await resp["Body"].content.read())


async def main():
    session = get_session()
    async with session.create_client(
            's3',
            region_name=AWS_REGION_NAME,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
    ) as s3_client:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector()) as session:
            cities = await get_cities(session)
            transfer_city_stats_tasks = [asyncio.create_task(transfer_city_stats_to_s3(session, s3_client, city)) for
                                         city in cities]
            await asyncio.gather(*transfer_city_stats_tasks)


@contextlib.asynccontextmanager
async def mock_boto():
    from moto.server import ThreadedMotoServer
    server = ThreadedMotoServer(port=0)

    server.start()
    port = server._server.socket.getsockname()[1]
    os.environ["AWS_ENDPOINT_URL"] = f"http://127.0.0.1:{port}"

    yield

    del os.environ["AWS_ENDPOINT_URL"]
    server.stop()


# TODO learn something about S3
# TODO push to S3 as soon as we get data from ref server
# TODO process data

async def main_mocked_boto():
    async with mock_boto():
        await main()


resp = asyncio.run(main_mocked_boto())
