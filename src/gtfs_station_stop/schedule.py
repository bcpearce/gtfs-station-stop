import asyncio
import os
from dataclasses import dataclass, field

from gtfs_station_stop.calendar import Calendar
from gtfs_station_stop.route_info import RouteInfo, RouteInfoDataset
from gtfs_station_stop.static_dataset import async_factory
from gtfs_station_stop.station_stop_info import StationStopInfo, StationStopInfoDataset
from gtfs_station_stop.trip_info import TripInfo, TripInfoDataset


@dataclass(kw_only=True)
class GtfsSchedule:
    calendar: Calendar = field(default_factory=Calendar)
    station_stop_info_ds: StationStopInfoDataset = field(
        default_factory=StationStopInfoDataset
    )
    trip_info_ds: TripInfoDataset = field(default_factory=TripInfoDataset)
    route_info_ds: RouteInfoDataset = field(default_factory=RouteInfoDataset)

    async def async_update_schedule(self, *gtfs_urls: os.PathLike, **kwargs):
        """Build a schedule dataclass."""
        async with asyncio.TaskGroup() as tg:
            cal_ds_task = tg.create_task(
                async_factory(self.calendar, *gtfs_urls, **kwargs)
            )
            ssi_ds_task = tg.create_task(
                async_factory(self.station_stop_info_ds, *gtfs_urls, **kwargs)
            )
            ti_ds_task = tg.create_task(
                async_factory(self.trip_info_ds, *gtfs_urls, **kwargs)
            )
            rti_ds_task = tg.create_task(
                async_factory(self.route_info_ds, *gtfs_urls, **kwargs)
            )
        self.calendar = cal_ds_task.result()
        self.station_stop_info_ds = ssi_ds_task.result()
        self.trip_info_ds = ti_ds_task.result()
        self.route_info_ds = rti_ds_task.result()

    def get_stop_info(self, stop_id: str) -> StationStopInfo | None:
        """Get stop info by ID."""
        return self.station_stop_info_ds.station_stop_infos.get(stop_id)

    def get_trip_headsign(self, trip_id: str) -> str:
        trip_info: TripInfo = self.trip_info_ds.get_close_match(trip_id)
        if trip_info is not None:
            return trip_info.trip_headsign
        return ""

    def get_route_color(self, route_id: str) -> str:
        route_info: RouteInfo = self.route_info_ds.get(route_id)
        if route_info is not None:
            return route_info.color
        return ""

    def get_route_text_color(self, route_id: str) -> str:
        route_info: RouteInfo = self.route_info_ds.get(route_id)
        if route_info is not None:
            return route_info.text_color
        return ""

    def get_route_type(self, route_id: str) -> str:
        route_info: RouteInfo = self.route_info_ds.get(route_id)
        if route_info is not None:
            return route_info.type.pretty_name()
        return ""


async def async_build_schedule(*gtfs_urls: os.PathLike, **kwargs):
    """Build a schedule dataclass."""
    async with asyncio.TaskGroup() as tg:
        cal_ds_task = tg.create_task(async_factory(Calendar, *gtfs_urls, **kwargs))
        ssi_ds_task = tg.create_task(
            async_factory(StationStopInfoDataset, *gtfs_urls, **kwargs)
        )
        ti_ds_task = tg.create_task(
            async_factory(TripInfoDataset, *gtfs_urls, **kwargs)
        )
        rti_ds_task = tg.create_task(
            async_factory(RouteInfoDataset, *gtfs_urls, **kwargs)
        )
    return GtfsSchedule(
        calendar=cal_ds_task.result(),
        station_stop_info_ds=ssi_ds_task.result(),
        trip_info_ds=ti_ds_task.result(),
        route_info_ds=rti_ds_task.result(),
    )
