from ...data import JSONDataConnector, DynamicDataConnector, Position


class _FlixTainmentDynamicConnector(JSONDataConnector, DynamicDataConnector):
    API_URL = "media.flixtrain.com"

    def refresh(self) -> None:
        self.store("position", "/services/pis/v1/position")
