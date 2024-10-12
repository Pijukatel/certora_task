import os
import socket

from types_aiobotocore_s3.literals import BucketLocationConstraintType

# Deployment is out of scope of the task. Simple string constants to be used as a configuration.
if os.environ.get("DOCKER_COMPOSE"):
    # Names used in docker compose
    # Make sure that settings here match what is written in docker-compose.yaml

    REFERENCE_SERVER_ADDRESS = socket.gethostbyname("ref_server")
    MOCKED_MOTO_SERVER_ADDRESS = socket.gethostbyname("mocked_moto")
    REFERENCE_SERVER_PORT = 8000
    MOCKED_MOTO_SERVER_PORT = 49638
else:
    # Local dev and debug
    REFERENCE_SERVER_ADDRESS = "127.0.0.1"
    MOCKED_MOTO_SERVER_ADDRESS = "127.0.0.1"
    REFERENCE_SERVER_PORT = 8000
    MOCKED_MOTO_SERVER_PORT = 49638


REFERENCE_SERVER = f"http://{REFERENCE_SERVER_ADDRESS}:{REFERENCE_SERVER_PORT}"
AWS_ACCESS_KEY_ID = "some_id"
AWS_SECRET_ACCESS_KEY = "some_key"
AWS_REGION_NAME: BucketLocationConstraintType = "us-west-2"
os.environ["AWS_ENDPOINT_URL"] = (
    f"http://{MOCKED_MOTO_SERVER_ADDRESS}:{MOCKED_MOTO_SERVER_PORT}"
)
AGGREGATED_STATS_FILE_NAME = "aggregated_stats"
