from __future__ import annotations

import logging

from ...third_party.unwired.apis import GenericUnwiredTrain, UnwiredJourneyMixin

logger = logging.getLogger(__name__)


class SBahnHannover(GenericUnwiredTrain, UnwiredJourneyMixin):
    """Implementation for the S-Bahn Hannover."""
