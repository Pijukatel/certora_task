import datetime
import json
from typing import Dict

from types_aiobotocore_s3 import S3Client
from botocore.exceptions import ClientError
from aiobotocore.session import get_session

from city_details_proccesing import create_city_stats_from_city_data
from configuration import AWS_REGION_NAME, AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID
from ref_server_communication import City


async def create_bucket(s3_client: S3Client, bucket_name: str) -> None:
    try:
        await s3_client.create_bucket(Bucket=bucket_name,
                                      CreateBucketConfiguration={"LocationConstraint": AWS_REGION_NAME})
    except ClientError as client_error:
        if client_error.response.get("Error", {}).get("Code", {}) != "BucketAlreadyOwnedByYou":
            # Do not raise if bucket already exists.
            raise client_error


def get_s3_client() -> S3Client:
    return get_session().create_client(
        's3',
        region_name=AWS_REGION_NAME,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
    )


async def push_city_stats_to_s3(city: City, date: datetime.date, raw_city_stats: bytes, s3_client: S3Client):
    # Expects existing buckets or other tasks already scheduled for creating them.
    await s3_client.get_waiter('bucket_exists').wait(Bucket=city.country,
                                                     WaiterConfig={"MaxAttempts": 2, "Delay": 2})


    stats = create_city_stats_from_city_data(json.loads(raw_city_stats))
    metadata: Dict[str, str] = {"bus-count": str(stats.bus_count),
                                "passenger-count": str(stats.passenger_count),
                                "exist-accident": str(int(stats.exist_accident)),
                                "average-delay-s": str(stats.average_delay_s)}

    await s3_client.put_object(Bucket=city.country,
                               Key=f"{date}/{city.name}",
                               Body=raw_city_stats,
                               Metadata=metadata,
                               ContentType='application/json')

