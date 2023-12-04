from datetime import datetime, timedelta
from typing import Generator

from ...._types import ID
from ... import ConnectingTrain
from ....data import (
    RESTDataConnector,
    ScheduledEvent,
    store,
)

# socket.io at /socket.io/


class InouiConnector(RESTDataConnector):
    API_URL = "https://wifi.sncf/router/api"

    @store('gps')
    def gps(self) -> dict:
        return self.get("train/gps").json()

    @store('details')
    def details(self) -> dict:
        return self.get("train/details").json()

    def trainboard(self, station_id: ID) -> dict:
        return self.get(f"information/trainboard/{station_id}")

    def refresh(self) -> None:
        self.gps()
        self.details()

        # self._data["attendance"] = self.get("bar/attendance").json()
        # self._data["auto"] = self.get("connection/activate/auto").json()
        # self._data["catalog"] = self.get("food/catalog").json()
        # self._data["coverage"] = self.get("train/coverage").json()
        # self._data["graph"] = self.get("train/graph").json()
        # self._data["modules"] = self.get("configuration/modules").json()
        # self._data["poi"] = self.get("poi").json()
        # self._data["registry"] = self.get("connection/registry").json()
        # self._data["room"] = self.get("chat/room").json()
        # self._data["statistics"] = self.get("connection/statistics").json()
        # self._data["status"] = self.get("connection/status").json()
        # self._data["videos"] = self.get("media/videos").json()
        # self._data["wordings"] = self.get("media/wordings", params=dict(language="de")).json()

    def connections(self, station_id: ID) -> Generator[ConnectingTrain, None, None]:
        for connection in self.trainboard(station_id).get("train", []):
            yield ConnectingTrain(
                vehicle_type=connection.get("type"),
                line_number=connection.get("num"),
                departure=ScheduledEvent(
                    scheduled=datetime.fromisoformat(connection.get("heure")),
                    actual=datetime.fromisoformat(connection.get("heure"))
                    + timedelta(minutes=int(connection.get("retard", 0))),
                ),
                destination=connection.get("origdest"),
                platform=ScheduledEvent(
                    scheduled=connection.get("attribut_voie"),
                    actual=connection.get("attribut_voie"),
                ),
            )
