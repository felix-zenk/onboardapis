from __future__ import annotations

from ...third_party.betria_interactive import FlightPath3DAPI


class FlyStreamAPI(FlightPath3DAPI):
    API_URL = 'https://fp3d-flystream.everhub.aero'
