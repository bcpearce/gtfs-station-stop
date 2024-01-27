import time

from gtfs_station_stop.feed_subject import FeedSubject


class StationStop:
    def __init__(self, stop_id: str, updater: FeedSubject):
        self.stop_id = stop_id
        self.updater = updater
        self.updater.subscribe(self)
        self.arrivals = []
        self.alerts = []
        self.last_updated = None

    def get_arrivals(self):
        return self.arrivals

    def get_time_to_arrivals(self):
        current_time = time.time()
        return [(id, (t - current_time)) for id, t in self.arrivals]

    def get_alerts(self):
        return self.alerts


import os  # noqa: E402
import sys  # noqa: E402

import dotenv  # noqa: E402

if __name__ == "__main__":
    dotenv.load_dotenv()
    fs = FeedSubject(
        os.environ["API_KEY"],
        [
            "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
            "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
            "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
            "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
            "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
            "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
            "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts",
        ],
    )

    ss = StationStop(sys.argv[1], fs)
    fs.update()
    print(f"Arrivals Raw: {ss.get_arrivals()}")
    print(f"Arrivals Rel: {ss.get_time_to_arrivals()}")
    print(f"      Alerts: {ss.get_alerts()}")
