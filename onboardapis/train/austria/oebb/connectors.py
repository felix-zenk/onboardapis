import time
from functools import lru_cache
from ....data import (
    RESTDataConnector,
    store,
)


class RailnetConnector(RESTDataConnector):
    API_URL = "https://railnet.oebb.at"

    @store('train_info')
    @lru_cache
    def train_info(self) -> dict:
        return self.get("api/trainInfo").json()

    @store('combined')
    def combined(self) -> dict:
        return self.get("/assets/modules/fis/combined.json", params={"_time": time.time()})

    def refresh(self) -> None:
        self.train_info()
        self.combined()
