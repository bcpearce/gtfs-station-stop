import os
from typing import Any

from gtfs_station_stop.helpers import gtfs_record_iter
from gtfs_station_stop.static_database import GtfsStaticDatabase


class RouteInfo:
    def __init__(self, route_data_dict: dict):
        self.agency_id = route_data_dict["agency_id"]
        self.id = route_data_dict["route_id"]
        self.short_name = route_data_dict["route_short_name"]
        self.long_name = route_data_dict["route_long_name"]
        self.type = route_data_dict["route_type"]
        self.desc = route_data_dict["route_desc"]
        self.url = route_data_dict.get("route_url")
        self.color = route_data_dict["route_color"]
        self.text_color = route_data_dict["route_text_color"]


class RouteInfoDatabase(GtfsStaticDatabase):
    def __init__(self, *gtfs_files: os.PathLike):
        self.route_infos = {}
        super().__init__(*gtfs_files)

    def add_gtfs_data(self, zip_filelike: os.PathLike):
        for line in gtfs_record_iter(zip_filelike, "routes.txt"):
            id = line["route_id"]
            self.route_infos[id] = RouteInfo(line)

    def get_routes(self):
        return self.route_infos.keys()

    def __getitem__(self, key):
        return self.route_infos[key]

    def get(self, key: str | None, default: Any | None = None):
        return self.route_infos.get(key, default)
