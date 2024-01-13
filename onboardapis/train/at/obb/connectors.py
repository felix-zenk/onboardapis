import time
from functools import lru_cache
from typing import TypedDict

from typing_extensions import deprecated

from ....data import (
    RESTDataConnector,
    store,
)

Endpoints = TypedDict("Endpoints", {
    'train_info': int,
    'gps': dict,
    'speed': float,
})


class RailnetRegioConnector(RESTDataConnector):
    API_URL = "https://railnet.oebb.at"

    @store('train_info')
    @lru_cache
    def train_info(self) -> int:
        return int(self.get("api/trainInfo").text)

    @store('gps')
    def gps(self) -> dict:
        return self.get("api/gps").json()

    @store('speed')
    def speed(self) -> float:
        return float(self.get("api/speed").text)

    @deprecated('combined has been removed from the API')
    @store('combined')
    def combined(self) -> dict:
        return self.get("assets/modules/fis/combined.json", params={"_time": time.time()}).json()

    def refresh(self) -> None:
        self.train_info()
        self.gps()
        self.speed()
