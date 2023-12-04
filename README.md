# onboardapis

[![PyPI-Versions](https://img.shields.io/pypi/pyversions/onboardapis)](https://pypi.org/project/onboardapis)
[![PyPI version](https://badge.fury.io/py/onboardapis.svg)](https://pypi.org/project/onboardapis)
[![build](https://img.shields.io/github/actions/workflow/status/felix-zenk/onboardapis/publish-to-pypi.yml?branch=main)](https://github.com/felix-zenk/onboardapis)
[![Documentation](https://img.shields.io/readthedocs/onboardapis)](https://onboardapis.readthedocs.io/en/latest/)
[![License](https://img.shields.io/github/license/felix-zenk/onboardapis)](https://github.com/felix-zenk/onboardapis/blob/main/LICENSE)

> **Warning**: Version `2.0.0` introduces breaking changes!

## Description

onboardapis allows you to interact with different on-board APIs.
You can connect to the Wi-Fi of a supported transportation provider
and access information about your journey, the vehicle you are travelling in and much more.

> **Note:** For now the only vehicle type covered by this package is trains.
> See the [supported APIs](#supported-apis) for more information.

---

## Installation

Install the latest version of onboardapis from [PyPI](https://pypi.org/project/onboardapis) using [pip](https://pip.pypa.io/en/stable/installation/):

```shell
$ python -m pip install onboardapis
```

---

## Quickstart

To begin with development you will need to know a few things first:

* What vehicle type you want to use
* Who operates the vehicle ([VKM register code](https://www.era.europa.eu/domains/registers/vkm_en) for trains from europe)
* What country is the operator from ([ISO 3166-2 country code](https://en.wikipedia.org/wiki/ISO_3166-2#Current_codes))

With this information you can get the needed module from the package 
``onboardapis.<vehicle-type>.<country>.<operator>`` 
and import the API class from it.

Let's say you want to use the on-board API called ICE Portal of Deutsche Bahn trains in Germany.

```python
from onboardapis.train.de.db import ICEPortal
```

Every vehicle has an ``init``-method that needs to be called to initialize the connection to the API.
When using a vehicle as a context manager the ``init``-method will automatically be called.

```python
from onboardapis.train.de.db import ICEPortal
from onboardapis.units import kilometers, kmh

train = ICEPortal()
train.init()  # Explicit call to init method to initialize API connection

print(
    "Travelling at", train.speed, "m/s",
    f"({kmh(ms=train.speed):.2f} km/h)",
    "with a delay of", train.delay, "seconds"
)

print(
    "Next stop:", train.current_station.name,
    "at", train.current_station.arrival.actual.strftime("%H:%M")
)

with ICEPortal() as train:  # init automatically called
    print(
        f"Distance to {train.current_station.name}:",
        f"{kilometers(meters=train.calculate_distance(train.current_station)):.1f} km"
    )
```

And there you go!
You can read more information about available attributes in the [trains documentation](https://onboardapis.readthedocs.io/en/latest/source/onboardapis.trains.html).

> As you may have noticed by now, the package always returns datetime or timedelta objects for time based values
> and other values like distances, velocity, etc. in SI units,
> so you have to convert to other units if you want to use values different from the SI units.
> For convenience the ``onboardapis.units`` module has functions to convert between units.

---

## Documentation
[![Documentation](https://img.shields.io/readthedocs/onboardapis)](https://onboardapis.readthedocs.io/en/latest/)

#### [ReadTheDocs](https://onboardapis.readthedocs.io/en/latest/)

## Supported APIs

| API          | Type  | Country      | Operator                           |
|--------------|-------|--------------|------------------------------------|
| RailnetRegio | train | at (austria) | obb (Österreichische Bundesbahnen) |
| ICEPortal    | train | de (germany) | db (Deutsche Bahn)                 |
| FlixTainment | train | de (germany) | flix (FlixTrain)                   |

## APIs in testing phase

| API              | Type  | Country      | Operator                                             |
|------------------|-------|--------------|------------------------------------------------------|
| PortalINOUI      | train | fr (france)  | sncf (Société nationale des chemins de fer français) |
| ZugPortal        | train | de (germany) | db (Deutsche Bahn)                                   |
| PortaleRegionale | train | it (italy)   | ti (Trenitalia)                                      |

## APIs in development

| API              | Type  | Country             | Operator                             |
|------------------|-------|---------------------|--------------------------------------|
