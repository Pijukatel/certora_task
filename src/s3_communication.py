import asyncio
import datetime
import json

from types_aiobotocore_s3 import S3Client
from botocore.exceptions import ClientError
from aiobotocore.session import get_session

from city_details_proccesing import create_city_stats_from_city_data, combine_stats, Stats, City
from configuration import AWS_REGION_NAME, AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID, AGGREGATED_STATS_FILE_NAME


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
    metadata = stats.create_s3_metadata_from_stats()

    # New data makes existing aggregated stats invalid. Delete them if they exist.
    await s3_client.delete_object(Bucket=city.country, Key=f"{date}/{AGGREGATED_STATS_FILE_NAME}")

    await s3_client.put_object(Bucket=city.country,
                               Key=f"{date}/{city.name}",
                               Body=raw_city_stats,
                               Metadata=metadata,
                               ContentType='application/json')


async def create_aggregated_stats_for_country_and_date(country: str, date: str, s3_client: S3Client) -> Stats:
    """Collect stats from metadata of files in country bucket with specific date and return combined stats."""
    data_files_info = (await s3_client.list_objects_v2(Bucket=country, Prefix=f"{date}/"))
    if "Contents" not in data_files_info:
        aggregated_stats = Stats(0, 0, False, 0)  # No data on this day in any city of this country.
    else:
        data_files = data_files_info["Contents"]
        get_metadata_tasks = [asyncio.create_task(s3_client.head_object(Bucket=country, Key=data_file["Key"])) for
                              data_file in data_files]
        await asyncio.gather(*get_metadata_tasks)
        stats = [Stats.create_stats_from_s3_metadata(task.result()["Metadata"]) for task in get_metadata_tasks]
        aggregated_stats = combine_stats(stats)

    await s3_client.put_object(Bucket=country,
                               Key=f"{date}/{AGGREGATED_STATS_FILE_NAME}",
                               Body=b"Aggregated stats file. Details in metadata",
                               Metadata=aggregated_stats.create_s3_metadata_from_stats(),
                               ContentType='application/json')
    return aggregated_stats


async def get_aggregated_stats_for_country_and_date(country: str, date: str, s3_client: S3Client) -> Stats:
    """Get existing stats or create new ones if there are no existing ones."""
    aggregated_file_key = f"{date}/{AGGREGATED_STATS_FILE_NAME}"
    try:
        metadata_of_aggregated_stats_file = (await s3_client.head_object(Bucket=country, Key=aggregated_file_key))[
            "Metadata"]
        return Stats.create_stats_from_s3_metadata(metadata_of_aggregated_stats_file)
    except ClientError:
        return await create_aggregated_stats_for_country_and_date(country, date, s3_client)
