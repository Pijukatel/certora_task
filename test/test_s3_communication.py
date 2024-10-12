import asyncio
import datetime
import json

import pytest
from botocore.exceptions import ClientError
from conftest import (
    EXAMPLE_COUNTRY_1,
    EXAMPLE_COUNTRY_2,
    EXAMPLE_ID_1,
    EXAMPLE_ID_2,
    generate_example_cities,
    generate_example_city_data,
)
from slugify import slugify

from city_details_proccesing import (
    City,
    Stats,
    combine_stats,
    create_city_stats_from_city_data,
)
from configuration import AGGREGATED_STATS_FILE_NAME
from s3_communication import (
    create_aggregated_stats_for_country_and_date,
    create_bucket,
    get_s3_client,
    push_city_stats_to_s3,
)


@pytest.mark.asyncio
async def test_data_pushed_to_s3_with_stats(run_dummy_moto):
    """Tests that data is correctly transferred from ref server to S3."""
    some_date = str(datetime.date(2024, 2, 1))
    example_city_data = generate_example_city_data(some_date)[EXAMPLE_ID_1]
    raw_city_stats = json.dumps(example_city_data).encode("utf-8")
    city = generate_example_cities()[EXAMPLE_ID_1]

    async with get_s3_client() as s3_client:
        await create_bucket(s3_client, city.country)
        await push_city_stats_to_s3(city, some_date, raw_city_stats, s3_client)

        metadata = await s3_client.head_object(
            Bucket=city.country, Key=f"{some_date}/{city.name}"
        )
        assert Stats.create_stats_from_s3_metadata(
            metadata["Metadata"]
        ) == create_city_stats_from_city_data(example_city_data)


@pytest.mark.asyncio
async def test_data_pushed_to_s3_with_deletes_existing_aggregated_stats(run_dummy_moto):
    """Tests that new data will delete related aggregated data as it has to be recalculated."""
    some_date = str(datetime.date(2024, 2, 1))
    example_city_data = generate_example_city_data(some_date)[EXAMPLE_ID_1]
    raw_city_stats = json.dumps(example_city_data).encode("utf-8")
    city = generate_example_cities()[EXAMPLE_ID_1]

    aggregated_file_key = f"{some_date}/{AGGREGATED_STATS_FILE_NAME}"

    async with get_s3_client() as s3_client:
        await create_bucket(s3_client, city.country)
        await s3_client.put_object(
            Bucket=city.country,
            Key=aggregated_file_key,
            Body=b"",
            ContentType="application/json",
        )
        await push_city_stats_to_s3(city, some_date, raw_city_stats, s3_client)

        with pytest.raises(ClientError) as client_error:
            await s3_client.head_object(Bucket=city.country, Key=aggregated_file_key)
        assert "Not Found" in str(client_error.value)


@pytest.mark.asyncio
async def test_create_aggregated_stats_for_country_and_date(run_dummy_moto):
    """Tests that data is correctly aggregated from relevant buckets and files.

    Test creates:
     -city data on relevant date in irrelevant bucket (should not be used in aggregation)
     -city data on irrelevant date in relevant bucket (should not be used in aggregation)
     -2x different cities' data in relevant bucket (should be used in aggregation)

     Verify that aggregated results are calculated only from cities from correct bucket and correct date.
    """
    # Arrange
    desired_date = str(datetime.date(2024, 2, 1))
    irrelevant_date = str(datetime.date(2024, 3, 1))
    desired_country = slugify(EXAMPLE_COUNTRY_1)
    irrelevant_country = slugify(EXAMPLE_COUNTRY_2)
    some_city_id = 3

    example_city_data_on_desired_date = generate_example_city_data(desired_date)[
        EXAMPLE_ID_1
    ]
    example_city_data_on_irrelevant_date = generate_example_city_data(irrelevant_date)[
        EXAMPLE_ID_2
    ]

    raw_city_stats_on_desired_date = json.dumps(
        example_city_data_on_desired_date
    ).encode("utf-8")
    raw_city_stats_on_irrelevant_date = json.dumps(
        example_city_data_on_irrelevant_date
    ).encode("utf-8")

    cities = generate_example_cities()
    relevant_city_1 = cities[EXAMPLE_ID_1]
    relevant_city_2 = cities[EXAMPLE_ID_2]
    city_in_irrelevant_country = City("Some_name", irrelevant_country, some_city_id)

    async with get_s3_client() as s3_client:
        create_desired_bucket_task = create_bucket(s3_client, desired_country)
        create_irrelevant_bucket_task = create_bucket(s3_client, irrelevant_country)
        await asyncio.gather(create_desired_bucket_task, create_irrelevant_bucket_task)

        push_data_from_desired_country_desired_date_tasks = [
            push_city_stats_to_s3(
                relevant_city_1, desired_date, raw_city_stats_on_desired_date, s3_client
            ),
            push_city_stats_to_s3(
                relevant_city_2, desired_date, raw_city_stats_on_desired_date, s3_client
            ),
        ]

        push_data_from_desired_country_irrelevant_date_task = push_city_stats_to_s3(
            relevant_city_1,
            irrelevant_date,
            raw_city_stats_on_irrelevant_date,
            s3_client,
        )
        push_data_from_irrelevant_country_desired_date_task = push_city_stats_to_s3(
            city_in_irrelevant_country,
            desired_date,
            raw_city_stats_on_desired_date,
            s3_client,
        )
        await asyncio.gather(
            *push_data_from_desired_country_desired_date_tasks,
            push_data_from_desired_country_irrelevant_date_task,
            push_data_from_irrelevant_country_desired_date_task,
        )

        expected_aggregated_results = combine_stats(
            [create_city_stats_from_city_data(example_city_data_on_desired_date)] * 2
        )

        # Act
        await create_aggregated_stats_for_country_and_date(
            desired_country, desired_date, s3_client
        )

        # Assert
        metadata_of_aggregated_stats_file = (
            await s3_client.head_object(
                Bucket=desired_country,
                Key=f"{desired_date}/{AGGREGATED_STATS_FILE_NAME}",
            )
        )["Metadata"]
        assert (
            Stats.create_stats_from_s3_metadata(metadata_of_aggregated_stats_file)
            == expected_aggregated_results
        )
