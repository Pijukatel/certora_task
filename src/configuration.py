import os
from types_aiobotocore_s3.literals import BucketLocationConstraintType
# Deployment is out of scope of the task. Simple string constants to be used as a configuration.
REFERENCE_SERVER_ADDRESS = "127.0.0.1"
REFERENCE_SERVER_PORT = 8000
REFERENCE_SERVER = f"http://{REFERENCE_SERVER_ADDRESS}:{REFERENCE_SERVER_PORT}"
AWS_ACCESS_KEY_ID = "some_id"
AWS_SECRET_ACCESS_KEY = "some_key"
AWS_REGION_NAME: BucketLocationConstraintType = "us-west-2"
MOCKED_MOTO_SERVER_PORT = 49638
os.environ["AWS_ENDPOINT_URL"] = f"http://127.0.0.1:{MOCKED_MOTO_SERVER_PORT}"
