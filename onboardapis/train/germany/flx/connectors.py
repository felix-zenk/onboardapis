from ....data import RESTDataConnector, store


class FlixTainmentConnector(RESTDataConnector):
    API_URL = "https://media.flixtrain.com"

    @store
    def position(self) -> dict:
        return self.get("services/pis/v1/position")

    def refresh(self) -> None:
        self.position()
