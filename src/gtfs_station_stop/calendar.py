import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from gtfs_station_stop.helpers import gtfs_record_iter


@dataclass
class Service:
    """Class for keeping calendar service data."""

    service_id: str
    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool
    start: datetime
    end: datetime

    exceptions: Iterable[datetime] = list


class Calendar:
    def __init__(self, gtfs_files: Iterable[os.PathLike] | os.PathLike | None = None):
        self._services = {}
        if gtfs_files is not None:
            if isinstance(gtfs_files, os.PathLike):
                gtfs_files = [gtfs_files]
            for file in gtfs_files:
                self.add_gtfs_data(file)

    def add_gtfs_data(self, zip_filelike):
        for line in gtfs_record_iter(zip_filelike, "calendar.txt"):
            self._services[line["service_id"]] = Service(
                line["service_id"],
                bool(int(line["monday"])),
                bool(int(line["tuesday"])),
                bool(int(line["wednesday"])),
                bool(int(line["thursday"])),
                bool(int(line["friday"])),
                bool(int(line["saturday"])),
                bool(int(line["sunday"])),
                datetime.strptime(line["start_date"], "%Y%m%d"),
                datetime.strptime(line["end_date"], "%Y%m%d") + timedelta(days=1),
            )

    def __getitem__(self, key) -> Service:
        return self._services[key]
