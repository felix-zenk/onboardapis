"""
Package for trains

## Operator ID

The operator ID for trains is different depending on the region.

For Europe, the operator ID is the [VKM register code](https://www.era.europa.eu/domains/registers/vkm_en).

---

Contains the following countries:

- ``onboardapis.train.at`` - Austria
- ``onboardapis.train.cz`` - Czechia
- ``onboardapis.train.de`` - Germany
- ``onboardapis.train.fr`` - France
- ``onboardapis.train.it`` - Italy

---
"""
from __future__ import annotations

import logging

from abc import ABCMeta
from dataclasses import dataclass
from typing import cast

from .. import Vehicle, Station, ConnectingVehicle
from ..data import ScheduledEvent

# noinspection PyUnresolvedReferences
from typing import Iterable  # for associations while generating docs
# noinspection PyUnresolvedReferences
from ..data import ID, Position  # noqa: F401  # for associations while generating docs
# noinspection PyUnresolvedReferences
from datetime import datetime  # noqa: F401  # for associations while generating docs

logger = logging.getLogger(__name__)


__all__ = [
    "at",
    "de",
    "fr",
    "it",
    "third_party",
    "TrainStation",
    "Train",
    "ConnectingTrain",
]


@dataclass
class TrainStation(Station):
    """
    An `onboardapis.Station` with the additional information of a platform
    """
    _connections: Iterable[ConnectingTrain]

    platform: ScheduledEvent[str] | None
    """The platform where the train arrives."""

    @property
    def connections(self) -> list[ConnectingTrain]:
        return cast(list[ConnectingTrain], super().connections)  # maybe force type instead of casting?


class Train(Vehicle, metaclass=ABCMeta):
    """
    Base class for all train implementations.
    """

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

    @property
    def type(self) -> str:
        """
        :return: The abbreviated train type
        :raises DataInvalidError: If the train type could not be fetched from the server
        """
        return 'undefined'

    @property
    def line_number(self) -> str:
        """
        :return: The line number
        :raises DataInvalidError: If the line number could not be fetched from the server
        """
        return 'undefined'


@dataclass
class ConnectingTrain(ConnectingVehicle):
    """
    A connecting train is a train that is not part of the main trip but of a connecting service

    It may only have limited information available
    """

    platform: ScheduledEvent[str] | None
    """
    The platform where the train will depart from
    """
