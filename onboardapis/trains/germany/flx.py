"""
Implementation of the german operator FLX (Flixtrain GmbH).
"""
from .. import Train, IncompleteTrainMixin
from ...utils.data import JSONDataConnector, DynamicDataConnector, Position

API_BASE_URL_FLIXTAINMENT = "media.flixtrain.com"


class _FlixTainmentDynamicConnector(DynamicDataConnector, JSONDataConnector):
    def __init__(self):
        super().__init__(API_BASE_URL_FLIXTAINMENT)

    def refresh(self) -> None:
        self.store("position", "/services/pis/v1/position")


class FlixTainment(IncompleteTrainMixin, Train):
    """
    Wrapper for interacting with the Flixtrain FLIXTainment API
    (few methods are available, because the API is very sparse)
    """
    def __init__(self):
        super().__init__()
        self._dynamic_data = _FlixTainmentDynamicConnector()

    def position(self) -> Position:
        return Position(
            latitude=self._dynamic_data.load("position", {}).get("latitude", None),
            longitude=self._dynamic_data.load("position", {}).get("longitude", None)
        )

    def speed(self) -> float:
        return float(self._dynamic_data.load("position", {}).get("speed", 0.0))  # float casting for linting

    # No more information available
