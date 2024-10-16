from typing import Any, Iterable

import pytest
from conftest import EXAMPLE_ID_1, EXAMPLE_ID_2, generate_example_city_data

from city_details_proccesing import (
    Stats,
    combine_stats,
    create_city_stats_from_city_data,
)


@pytest.mark.parametrize(
    "city_data, expected_city_stats_per_day",
    (
        (
            generate_example_city_data("irrelevant")[EXAMPLE_ID_1],
            Stats(
                bus_count=2,
                passenger_count=30,
                exist_accident=True,
                average_delay_s=150,
            ),
        ),
        (
            generate_example_city_data("irrelevant")[EXAMPLE_ID_2],
            Stats(
                bus_count=2,
                passenger_count=70,
                exist_accident=False,
                average_delay_s=350,
            ),
        ),
    ),
)
def test_create_city_stats_for_day(
    city_data: list[dict[str, Any]], expected_city_stats_per_day: Stats
):
    assert create_city_stats_from_city_data(city_data) == expected_city_stats_per_day


@pytest.mark.parametrize(
    "input_stats, expected_combined_stats",
    (
        (
            (
                create_city_stats_from_city_data(stats)
                for stats in generate_example_city_data("irrelevant").values()
            ),
            Stats(
                bus_count=6,
                passenger_count=210,
                exist_accident=True,
                average_delay_s=350,
            ),
        ),
        (
            [
                create_city_stats_from_city_data(
                    generate_example_city_data("irrelevant")[EXAMPLE_ID_1]
                )
            ]
            * 2,
            Stats(
                bus_count=4,
                passenger_count=60,
                exist_accident=True,
                average_delay_s=150,
            ),
        ),
        (
            [
                create_city_stats_from_city_data(
                    generate_example_city_data("irrelevant")[EXAMPLE_ID_2]
                )
            ]
            * 2,
            Stats(
                bus_count=4,
                passenger_count=140,
                exist_accident=False,
                average_delay_s=350,
            ),
        ),
    ),
)
def test_combine_stats(input_stats: Iterable[Stats], expected_combined_stats: Stats):
    assert combine_stats(input_stats) == expected_combined_stats


@pytest.mark.parametrize(
    "exist_accident_str_representation, exist_accident_bool_representation",
    (("0", False), ("1", True)),
)
def test_create_stats_from_s3_metadata(
    exist_accident_str_representation: str, exist_accident_bool_representation: bool
):
    metadata = {
        "bus-count": "1",
        "passenger-count": "10",
        "exist-accident": exist_accident_str_representation,
        "average-delay-s": "20",
    }
    assert Stats.create_stats_from_s3_metadata(metadata) == Stats(
        1, 10, exist_accident_bool_representation, 20
    )
