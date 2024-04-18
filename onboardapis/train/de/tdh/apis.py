from __future__ import annotations

import logging

from ...third_party.unwired import GenericUnwiredTrain, GenericUnwiredAPI, GenericUnwiredInternetAccessInterface
from ...third_party.unwired.mixins import UnwiredJourneyMixin

logger = logging.getLogger(__name__)


class SBahnHannover(GenericUnwiredTrain, UnwiredJourneyMixin):
    """Implementation for the S-Bahn Hannover."""

    def __init__(self) -> None:
        self._api = GenericUnwiredAPI()
        self._internet_access = GenericUnwiredInternetAccessInterface()
        GenericUnwiredTrain.__init__(self)
        UnwiredJourneyMixin.__init__(self)
