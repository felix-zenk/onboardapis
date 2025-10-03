"""
### Work in progress!

This module contains the implementation for the estonian operator Marabu Airlines OÜ.

> Lists Everhub as the portal provider. Uses websockets primarily!
"""
from __future__ import annotations

from .third_party.betria_interactive import FlightPath3DAPI
from .third_party.inflight_dublin import Everhub


class UnnamedWideroePortal(Everhub):
    _api = FlightPath3DAPI(url='https://fp3d-wideroe.everhub.aero')
