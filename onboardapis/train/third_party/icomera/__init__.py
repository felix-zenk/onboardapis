"""
Implementation for the Icomera AB Passenger Wi-Fi.
"""
from __future__ import annotations

from .apis import GenericIcomeraTrain
from .interfaces import GenericIcomeraAPI

__all__ = [
    "GenericIcomeraTrain",
    "GenericIcomeraAPI",
]
