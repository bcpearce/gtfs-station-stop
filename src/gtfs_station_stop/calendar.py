import os
from collections.abc import Iterable
from datetime import date, datetime
from typing import NamedTuple

from gtfs_station_stop.helpers import gtfs_record_iter

SERVICE_EXCEPTION_TYPE_ADDED = "1"
SERVICE_EXCEPTION_TYPE_REMOVED = "2"


class ServiceDays(NamedTuple):
    """Class for storing the days available with names."""

    monday: bool
    tuesday: bool
    wednesday: bool
    thursday: bool
    friday: bool
    saturday: bool
    sunday: bool

    def no_service():
        return ServiceDays(*[False] * len(ServiceDays._fields))


class Service:
    """Class for keeping calendar service data."""

    def __init__(
        self, service_id: str, service_days: ServiceDays, start: date, end: date
    ):
        self.service_id = service_id
        self.service_days = service_days
        self.start = start
        self.end = end
        self.added_exceptions = set()
        self.removed_exceptions = set()

    def is_active_on(self, the_date: date | None = None):
        """Check if service is active on a given datetime, defaults to now."""
        if isinstance(the_date, datetime):
            the_date = the_date.date()
        if the_date is None:
            the_date = date.today()
        normally_active = (self.start <= the_date <= self.end) and self.service_days[
            the_date.weekday()
        ]
        return (normally_active and the_date not in self.removed_exceptions) or (
            not normally_active and the_date in self.added_exceptions
        )

    def no_regular_service(service_id: str):
        return Service(service_id, ServiceDays.no_service(), date.min, date.min)


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
                ServiceDays(
                    line["monday"] == "1",
                    line["tuesday"] == "1",
                    line["wednesday"] == "1",
                    line["thursday"] == "1",
                    line["friday"] == "1",
                    line["saturday"] == "1",
                    line["sunday"] == "1",
                ),
                datetime.strptime(line["start_date"], "%Y%m%d").date(),
                datetime.strptime(line["end_date"], "%Y%m%d").date(),
            )
        # Add in special services
        for line in gtfs_record_iter(zip_filelike, "calendar_dates.txt"):
            service_id = line["service_id"]
            if self._services.get(service_id) is None:
                # Create a blank calendar if it is missing
                self._services[service_id] = Service.no_regular_service(service_id)
            if line["exception_type"] == SERVICE_EXCEPTION_TYPE_ADDED:
                self._services[service_id].added_exceptions.add(
                    datetime.strptime(line["date"], "%Y%m%d").date()
                )
            elif line["exception_type"] == SERVICE_EXCEPTION_TYPE_REMOVED:
                self._services[service_id].removed_exceptions.add(
                    datetime.strptime(line["date"], "%Y%m%d").date()
                )
            else:
                raise RuntimeError("Unsupported GTFS service exception type.")

    def __getitem__(self, key) -> Service:
        return self._services[key]
