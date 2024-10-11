import dataclasses
from isodate import parse_duration  # type:ignore[import-untyped] # Stub files not published
from typing import Any, Iterable


@dataclasses.dataclass
class Stats():
    """Represents stats from one city in one day or cumulative stats from many cities in one day.
    """
    bus_count: int
    passenger_count: int
    exist_accident: bool
    average_delay_s: int


def is_city_data_valid(city_data: list[dict[str, Any]]) -> bool:
    """Placeholder for input data validation. Out of scope."""
    return True


def create_stats_from_s3_metadata(metadata: dict[str,str]):
    return Stats(bus_count = int(metadata["bus-count"]),
                 passenger_count=int(metadata["passenger-count"]),
                 exist_accident= bool(int((metadata["exist-accident"]))),
                 average_delay_s = int(metadata["average-delay-s"]))

def create_city_stats_from_city_data(city_data: list[dict[str, Any]]):
    """Creates single city single day stats."""
    if not is_city_data_valid(city_data):
        raise ValueError("Invalid input data!")

    total_delay_s = 0
    total_passangers = 0
    exist_accident = False
    bus_count = len(city_data)
    for bus_details in city_data:
        total_delay_s += parse_duration(bus_details["delay"]).total_seconds()
        total_passangers += bus_details["passengers"]
        exist_accident = exist_accident or bus_details["accident"]

    return Stats(bus_count=bus_count,
                 passenger_count=total_passangers, exist_accident=exist_accident,
                 average_delay_s=round(total_delay_s / bus_count))


def combine_stats(mupltiple_stats: Iterable[Stats]) -> Stats:
    """Combine multiple stats to single aggregated result."""
    total_delay_s = 0
    total_passangers = 0
    exist_accident = False
    bus_count = 0
    for single_stats in mupltiple_stats:
        total_delay_s += single_stats.average_delay_s * single_stats.bus_count
        total_passangers += single_stats.passenger_count
        exist_accident = exist_accident or single_stats.exist_accident
        bus_count += single_stats.bus_count

    return Stats(bus_count=bus_count,
                 passenger_count=total_passangers, exist_accident=exist_accident,
                 average_delay_s=total_delay_s // bus_count)
