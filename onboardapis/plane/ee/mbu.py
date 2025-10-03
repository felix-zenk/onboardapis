"""
### Work in progress!

This module contains the implementation for the Estonian operator Marabu Airlines OÜ.
"""
from __future__ import annotations

from ..third_party.betria_interactive import FlightPath3DAPI
from ..third_party.inflight_dublin import Everhub


class UnnamedMarabuPortal(Everhub):
    _api = FlightPath3DAPI(url='https://fp3d-marabu.everhub.aero')
