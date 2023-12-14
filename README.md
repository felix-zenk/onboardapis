# onboardapis

[![Python versions](https://img.shields.io/pypi/pyversions/onboardapis)](https://pypi.org/project/onboardapis)
[![PyPI version](https://badge.fury.io/py/onboardapis.svg)](https://pypi.org/project/onboardapis)
![Build status](https://img.shields.io/github/actions/workflow/status/felix-zenk/onboardapis/build.yml?branch=main)
[![Documentation status](https://img.shields.io/github/actions/workflow/status/felix-zenk/onboardapis/docs.yml?label=docs)](https://felix-zenk.github.io/onboardapis/docs/)
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

Install the latest stable version of onboardapis
from [PyPI](https://pypi.org/project/onboardapis)
using [pip](https://pip.pypa.io/en/stable/installation/):

```shell
$ python -m pip install onboardapis
```

![Version](https://img.shields.io/pypi/v/onboardapis?label=%20)
[![Documentation (v1.3.1)](https://img.shields.io/badge/Docs_v1.3.1-_?color=3581b6)](https://onboardapis.readthedocs.io/en/stable/)

---

Install the latest development version of onboardapis
from [GitHub](https://github.com/felix-zenk/onboardapis)
using [pip](https://pip.pypa.io/en/stable/installation/):

```shell
$ python -m pip install git+https://github.com/felix-zenk/onboardapis.git
```

![Version](https://img.shields.io/badge/v2.0.0-%20?color=1081c2)

---

Clone the repository
from [GitHub](https://github.com/felix-zenk/onboardapis)
and install the package in development mode:

```shell
$ git clone https://github.com/felix-zenk/onboardapis.git
$ cd onboardapis
$ python -m pip install -e .
```

![Version](https://img.shields.io/badge/v2.0.0-%20?color=1081c2)

---

## Quickstart

To begin with development you will need to know a few things first:

* What vehicle type you want to use
* Who operates the vehicle
* What country is the operator from

With this information you can get the needed module from the package 
``onboardapis.<vehicle-type>.<country-code>.<operator-code>`` 
and import the API class from it.
Read more on finding the API you are looking for in [Finding your API](#find-your-api)

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
You can read more information about available attributes in the [trains documentation](https://felix-zenk.github.io/onboardapis/docs/train/index.html#onboardapis.train.Train).

> As you may have noticed by now, the package always returns datetime or timedelta objects for time based values
> and other values like distances, velocity, etc. in SI units,
> so you have to convert to other units if you want to use values different from the SI units.
> For convenience the ``onboardapis.units`` module has functions to convert between units.

---

## Documentation
[![Documentation status](https://img.shields.io/github/actions/workflow/status/felix-zenk/onboardapis/docs.yml?label=docs)](https://felix-zenk.github.io/onboardapis/docs/)

#### Read more on [GitHub-Pages](https://felix-zenk.github.io/onboardapis/docs/)


## Supported APIs

| API           | [API scope](#api-scope) | Type  | Country      | Operator                                  |
|---------------|-------------------------|-------|--------------|-------------------------------------------|
| RailnetRegio  | full                    | train | at (austria) | obb (Österreichische Bundesbahnen)        |
| ICEPortal     | full                    | train | de (germany) | db (Deutsche Bahn)                        |
| FlixTainment  | geo                     | train | de (germany) | flix (FlixTrain)                          |
| CaptivePortal | basic                   | train | de (germany) | me (metronom Eisenbahngesellschaft) / bth |

## APIs in testing phase

| API              | [API scope](#api-scope) | Type  | Country      | Operator                                             |
|------------------|-------------------------|-------|--------------|------------------------------------------------------|
| PortalINOUI      | full                    | train | fr (france)  | sncf (Société nationale des chemins de fer français) |
| ZugPortal        | full                    | train | de (germany) | db (Deutsche Bahn)                                   |
| PortaleRegionale | journey-simple          | train | it (italy)   | ti (Trenitalia)                                      |

## APIs in development

| API           | [API scope](#api-scope) | Type  | Country             | Operator                                                                 |
|---------------|-------------------------|-------|---------------------|--------------------------------------------------------------------------|
| Transdev      | journey-simple          | train | de (germany)        | tdh (Transdev Hannover GmbH)                                             |


## Find your API

##### 1. Vehicle type: ``train``, ``plane``, ``bus``, ``ship``, ``other``.
##### 2. [ISO 3166-2 country code](https://en.wikipedia.org/wiki/ISO_3166-2#Current_codes)
##### 3. Operator code

| Vehicle type | Region | Register                                                    |
|--------------|--------|-------------------------------------------------------------|
| plane        | global | [ICAO](https://en.wikipedia.org/wiki/List_of_airline_codes) |
| train        | europe | [VKM](https://www.era.europa.eu/domains/registers/vkm_en)   |


# API scope

The API scope defines what information can be accessed through the API and is a general indicator of the API's quality.
The currently possible API scopes are:
- ``basic``: Only basic information is available such as connection status to the API.
- ``vehicle``: The API supplies information about the vehicle such as the train ID, line number, etc.
- ``geo``: The API supplies information about the current location, speed, etc. of the vehicle.
- ``journey-simple``: The API supplies simple journey information including the current station and the destination station.
- ``journey``: The API supplies detailed journey information including the all station and possibly connecting trains.
- ``full``: All of the above.
