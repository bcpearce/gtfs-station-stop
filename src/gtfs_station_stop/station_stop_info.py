import os
from typing import Any

from gtfs_station_stop.helpers import gtfs_record_iter
from gtfs_station_stop.static_database import GtfsStaticDatabase


class StationStopInfo:
    pass


class StationStopInfo:
    def __init__(self, parent: StationStopInfo, station_data_dict: dict):
        self.id = station_data_dict["stop_id"]
        self.name = station_data_dict["stop_name"]
        self.lat = station_data_dict.get("stop_lat")
        self.lon = station_data_dict.get("stop_lon")
        self.parent = parent

    def __repr__(self):
        return f"{self.id}: {self.name}, lat: {self.lat}, long: {self.lon}{f', parent: {self.parent.id}' if self.parent else ''}"


class StationStopInfoDatabase(GtfsStaticDatabase):
    def __init__(self, *gtfs_files: os.PathLike):
        self.station_stop_infos = {}
        super().__init__(*gtfs_files)

    def add_gtfs_data(self, zip_filelike):
        for line in gtfs_record_iter(zip_filelike, "stops.txt"):
            id = line["stop_id"]
            parent = self.station_stop_infos.get(line["parent_station"])
            self.station_stop_infos[id] = StationStopInfo(parent, line)

    def get_stop_ids(self) -> list[str]:
        return self.station_stop_infos.keys()

    def __getitem__(self, key) -> StationStopInfo:
        return self.station_stop_infos[key]

    def get(self, key: Any, default: Any | None = None):
        return self.station_stop_infos.get(key, default)
