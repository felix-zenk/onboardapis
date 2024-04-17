from __future__ import annotations

import logging

from ...third_party.unwired import GenericUnwiredTrain, GenericUnwiredAPI
from ...third_party.unwired.mixins import UnwiredJourneyMixin

logger = logging.getLogger(__name__)


class SBahnHannover(GenericUnwiredTrain, UnwiredJourneyMixin):
    """Implementation for the S-Bahn Hannover."""

    def init(self) -> None:
        self._api = GenericUnwiredAPI()
        GenericUnwiredTrain.__init__(self)
        UnwiredJourneyMixin.__init__(self)
