import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from gtfs_station_stop.static_dataset import GtfsStaticDataset


class LocationType(Enum):
    """
    Location Type.
    see https://gtfs.org/documentation/schedule/reference/#stopstxt
    """

    STOP = 0
    STATION = 1
    ENTRANCE = 2
    GENERIC_NODE = 3
    BOARDING_AREA = 4


class StationStopInfo:
    pass


class StationStopInfo:
    """Class for a Station/Stop Dataset Record"""

    def __init__(
        self, station_data_dict: dict, parent: StationStopInfo | None = None
    ) -> None:
        self.parent_station = station_data_dict.get("parent_station")
        self.location_type = StationStopInfo._get_location_type(
            station_data_dict.get("location_type", "")
        )
        self.id = station_data_dict["stop_id"]
        self.code = station_data_dict.get("stop_code")
        self.name = station_data_dict.get("stop_name")
        self.desc = station_data_dict.get("stop_desc")
        self.lat = station_data_dict.get("stop_lat")
        self.lon = station_data_dict.get("stop_lon")
        self.url = station_data_dict.get("stop_url")

        self.parent = parent

    @staticmethod
    def _get_location_type(raw: str) -> LocationType:
        if raw == "":
            return LocationType.STOP
        return LocationType(int(raw))

    def __repr__(self):
        return f"{self.id}: {self.name}, lat: {self.lat}, long: {self.lon}{f', parent: {self.parent.id}' if self.parent else ''}"  # noqa E501


@dataclass
class StationStopInfoDataset(GtfsStaticDataset):
    """Dataset class for Station/Stop Info."""

    station_stop_infos: dict[str, StationStopInfo]

    def __init__(self, *gtfs_files: os.PathLike, **kwargs):
        self.station_stop_infos = {}
        super().__init__(*gtfs_files, **kwargs)

    def add_gtfs_data(self, zip_filelike):
        for line in self._get_gtfs_record_iter(zip_filelike, "stops.txt"):
            stop_id = line["stop_id"]
            parent = None
            if line.get("parent_station"):
                parent = self.station_stop_infos.get(line["parent_station"])
            self.station_stop_infos[stop_id] = StationStopInfo(line, parent)

    def get_stop_ids(self) -> list[str]:
        """Get all stop IDs."""
        return self.station_stop_infos.keys()

    def __getitem__(self, key) -> StationStopInfo:
        return self.station_stop_infos[key]

    def get(self, key: Any, default: Any | None = None):
        """Get a stop by ID or a default."""
        return self.station_stop_infos.get(key, default)
