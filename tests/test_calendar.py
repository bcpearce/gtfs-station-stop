from datetime import date, datetime

from gtfs_station_stop.calendar import Calendar


def test_invalid_gtfs_zip(test_directory):
    assert Calendar() == Calendar(
        test_directory / "data" / "gtfs_static_nocalendar.zip"
    )


def test_get_station_stop_info_from_zip_calendar_txt(gtfs_calendar):
    service = gtfs_calendar["Regular"]
    # GTFS Data for test has Regular Service active on all weekdays, but not weekends
    assert service.is_active_on(datetime(year=2024, month=3, day=4)) is True, (
        "Regular Service active on a weekday."
    )
    assert service.is_active_on(datetime(year=2024, month=3, day=9)) is False, (
        "Regular Service not active on a weekend."
    )
    # Test with date too
    assert service.is_active_on(date(year=2024, month=3, day=4)) is True, (
        "Regular Service active on a weekday."
    )
    assert service.is_active_on(date(year=2024, month=3, day=9)) is False, (
        "Regular Service not active on a weekend."
    )


def test_get_station_stop_info_from_zip_calendar_dates_txt(gtfs_calendar):
    assert (
        gtfs_calendar["Regular"].is_active_on(date(year=2024, month=12, day=25))
        is False
    ), "No Regular service on Christmas."
    assert (
        gtfs_calendar["PiDaySpecial"].is_active_on(date(year=2024, month=3, day=14))
        is True
    ), "Service 'PiDaySpecial' should be added for 2024-03-14."

    assert (
        gtfs_calendar["PiDaySpecial"].is_active_on(date(year=2024, month=3, day=13))
        is False
    ), "Service PiDaySpecial should not be active for 2024-03-13."


def test_reading_calendar_with_leading_spaces(test_directory):
    gtfs_calendar = Calendar(test_directory / "data" / "gtfs_calendar_with_spaces.zip")
    assert len(gtfs_calendar.services) == 3
