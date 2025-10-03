"""
### Work in progress!

This module contains the implementation for the czech operator Smartwings, a.s.
"""
from __future__ import annotations

from .third_party.betria_interactive import FlightPath3DAPI
from .third_party.inflight_dublin import Everhub


class UnnamedSmartwingsPortal(Everhub):
    _api = FlightPath3DAPI(url='https://fp3d-mywingstv.everhub.aero')
