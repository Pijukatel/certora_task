from types_aiobotocore_s3 import S3Client
from botocore.exceptions import ClientError
from aiobotocore.session import get_session
from configuration import AWS_REGION_NAME, AWS_SECRET_ACCESS_KEY, AWS_ACCESS_KEY_ID


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


async def push_city_stats_to_s3(city, date, raw_city_stats, s3_client):
    # Expects existing buckets or other tasks already scheduled for creating them.
    await s3_client.get_waiter('bucket_exists').wait(Bucket=city.country,
                                                     WaiterConfig={"MaxAttempts": 2, "delay": 2})
    await s3_client.put_object(Bucket=city.country, Key=f"{city.name}/{date}", Body=raw_city_stats,
                               ContentType='application/json')
