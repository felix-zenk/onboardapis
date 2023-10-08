from datetime import datetime, timedelta
from typing import Literal, Generator

from ... import ConnectingTrain
from ....exceptions import APIConnectionError
from ....data import (
    JSONDataConnector,
    StaticDataConnector,
    DynamicDataConnector,
    ScheduledEvent,
    some_or_default,
)


class ICEPortalStaticConnector(JSONDataConnector, StaticDataConnector):
    __slots__ = []

    API_URL = "iceportal.de"

    def refresh(self):
        # Bestellen am Platz
        self.store("bap", self._get("/bap/api/bap-service-status"))
        # train names (optional)
        try:
            self.store(
                "names",
                self._get(
                    "/projects/onboardapis/res/train/germany/db/names.json",
                    base_url="felix-zenk.github.io",
                ),
            )
        # Try to get the names from GitHub. If there is no internet connection, then don't use names.
        except ConnectionError:
            self.store("names", {})


class ICEPortalDynamicConnector(JSONDataConnector, DynamicDataConnector):
    __slots__ = ["_connections_cache_control"]

    API_URL = "iceportal.de"

    def __init__(self):
        super().__init__()
        self._connections_cache_control = {}
        """
        A cache for connections
        Connections for DB are only available shortly before the arrival
        -> Cache every already seen connection as well
        """

    def refresh(self):
        # status
        self.store("status", self._get("/api1/rs/status"))
        # trip
        self.store("trip", self._get("/api1/rs/tripInfo/trip"))

    def connections(self, station_id: str) -> Generator[ConnectingTrain, None, None]:
        """
        Get all connections for a station

        :param station_id: The station to get the connections for
        :type station_id: str
        :return: A generator yielding a list of connections for the station
        :rtype: Generator[list[ConnectingTrain]]
        """

        # Function to determine when to update the cache
        def cache_valid() -> bool:
            last_update = self._connections_cache_control.get(station_id, {}).get(
                "last_update"
            )
            if last_update is None:
                return False
            return datetime.now() < last_update + timedelta(minutes=1)

        # Let the cache expire after 1 minute
        if cache_valid():
            yield from self.load(f"connections_{station_id}", [])
            return

        # Request the connections
        try:
            connections_json = self._get(f"/api1/rs/tripInfo/connection/{station_id}")
        except APIConnectionError:
            # Try to return the last cached connections if new connections could not be fetched
            yield from self.load(f"connections_{station_id}", [])
            return

        # Process the connections
        connections = list(
            [
                ConnectingTrain(
                    vehicle_type=connection.get("trainType", None),
                    line_number=connection.get("vzn", None),
                    platform=ScheduledEvent(
                        scheduled=connection.get("track", {}).get("scheduled", None),
                        actual=connection.get("track", {}).get("actual", None),
                    ),
                    destination=connection.get("station", {}).get("name", None),
                    departure=ScheduledEvent(
                        scheduled=(
                            datetime.fromtimestamp(
                                int(
                                    some_or_default(
                                        connection.get("timetable", {}).get(
                                            "scheduledDepartureTime"
                                        ),
                                        default=0,
                                    )
                                )
                                / 1000
                            )
                            if some_or_default(
                                connection.get("timetable", {}).get(
                                    "scheduledDepartureTime"
                                )
                            )
                            is not None
                            else None
                        ),
                        actual=(
                            datetime.fromtimestamp(
                                (
                                    some_or_default(
                                        connection.get("timetable", {}).get(
                                            "actualDepartureTime"
                                        ),
                                        default=0,
                                    )
                                )
                                / 1000
                            )
                            if some_or_default(
                                connection.get("timetable", {}).get(
                                    "actualDepartureTime"
                                )
                            )
                            is not None
                            else None
                        ),
                    ),
                )
                for connection in connections_json.get("connections", [])
            ]
        )
        self.store(f"connections_{station_id}", connections)
        self._connections_cache_control[station_id] = {"last_update": datetime.now()}
        yield from connections
        return


class ZugPortalStaticConnector(JSONDataConnector, StaticDataConnector):
    API_URL = "zugportal.de"

    def refresh(self):
        pass


class ZugPortalDynamicConnector(JSONDataConnector, DynamicDataConnector):
    API_URL = "zugportal.de"

    def refresh(self):
        self.store("journey", self._get("/@prd/zupo-travel-information/api/public/ri/journey"))
        journey_id = None
        self.store("current_journey", self._get(f"/@prd/zupo-travel-information/api/public/ri/journey/{journey_id}"))
