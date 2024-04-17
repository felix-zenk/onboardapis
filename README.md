onboardapis
===

[![Python versions](https://img.shields.io/pypi/pyversions/onboardapis)](https://pypi.org/project/onboardapis)
[![PyPI version](https://badge.fury.io/py/onboardapis.svg)](https://pypi.org/project/onboardapis)
[![Build package](https://github.com/felix-zenk/onboardapis/actions/workflows/build.yml/badge.svg)](https://github.com/felix-zenk/onboardapis/actions/workflows/build.yml)
[![Deploy documentation](https://github.com/felix-zenk/onboardapis/actions/workflows/docs.yml/badge.svg)](https://github.com/felix-zenk/onboardapis/actions/workflows/docs.yml)
[![License](https://img.shields.io/github/license/felix-zenk/onboardapis)](https://github.com/felix-zenk/onboardapis/blob/main/LICENSE)

> **Warning**: Version `2.0.0` introduces breaking changes! Existing code will definitely not work anymore.

## Description

onboardapis allows you to interact with different on-board APIs.
You can connect to the Wi-Fi of a supported transportation provider
and access information about your journey, the vehicle you are travelling in and much more.

> **Note:** The only vehicle type covered by this package currently is `train`.
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
``onboardapis.<type>.<country>.<operator>`` and import the API class from it.
For more specific information on finding the API you are looking for,
see [Finding your API](#find-your-api).

> **Example**: Let's say you want to use the on-board API called ICE Portal of Deutsche Bahn trains in Germany:
> ```python
> from onboardapis.train.de.db import ICEPortal
> ```

Every vehicle has an ``init``-method that needs to be called to initialize the connection to the API.
When using a vehicle as a context manager the ``init``-method will automatically be called.

```python
from onboardapis.train.de.db import ICEPortal
from onboardapis.units import kilometers, kmh


# init is automatically called
with ICEPortal() as train:
    print(
        f"Distance to {train.current_station.name}:",
        f"{kilometers(meters=train.calculate_distance(train.current_station)):.1f} km"
    )


# init has to be explicitly called
train = ICEPortal()
train.init()  # Explicit call to init method to initialize API connection

print(
    f"Travelling at {train.speed} m/s",
    f"({kmh(ms=train.speed):.2f} km/h)",
    f"with a delay of {train.delay.total_seconds():.0f} seconds"
)
```

And there you go!  
You can read more information about available attributes in the ``onboardapis.train.Train`` and ``onboardapis.mixins`` documentation
and the respective train's documentation.

> **Note**: As you may have noticed by now, the package always returns `datetime` or `timedelta` objects for time based values
> and other values like distances, velocity, etc. in SI units,
> so you have to convert to other units if you want to use values different from the SI units.
> For convenience the ``onboardapis.units`` module provides functions to convert between units.
>
> The name of a conversion function is the unit which will be the result of the conversion.
> Different units can be passed to a conversion function as keywords.
> Keywords can be combined to return the sum of the input units.

---

## Documentation
[![GitHub-Pages](https://github.com/felix-zenk/onboardapis/actions/workflows/docs.yml/badge.svg)](https://felix-zenk.github.io/onboardapis/)

#### Access the documentation on [GitHub-Pages](https://felix-zenk.github.io/onboardapis/).


## Supported APIs

| API                   | [API scope](#api-scope) | Type  | Country      | Operator                                                                           |
|-----------------------|-------------------------|-------|--------------|------------------------------------------------------------------------------------|
| RailnetRegio          | geo                     | train | at (Austria) | obb (Österreichische Bundesbahnen)                                                 |
| ICEPortal             | full                    | train | de (Germany) | db (Deutsche Bahn / DB AG)                                                         |
| FlixTainment          | geo                     | train | de (Germany) | flix (Flix Train GmbH)                                                             |
| MetronomCaptivePortal | basic                   | train | de (Germany) | me (metronom Eisenbahngesellschaft mbH) / bth (ALSTOM Transportation Germany GmbH) |

## Experimental APIs

| API              | [API scope](#api-scope) | Type  | Country      | Operator                     |
|------------------|-------------------------|-------|--------------|------------------------------|
| PortalINOUI      | full                    | train | fr (France)  | sncf (SNCF Voyageurs)        |
| ZugPortal        | full                    | train | de (Germany) | db (Deutsche Bahn / DB AG)   |
| PortaleRegionale | journey-simple          | train | it (Italy)   | ti (Trenitalia S.p.A.)       |
| SBahnHannover    | journey-simple          | train | de (Germany) | tdh (Transdev Hannover GmbH) |

## APIs in development

| API  | [API scope](#api-scope) | Type  | Country | Operator |
|------|-------------------------|-------|---------|----------|
| ...  |                         |       |         |          |

## Find your API

##### 1. Determine vehicle type: ``train``, ``plane``, ``bus``, ``ship``, ``other``.
##### 2. Find the [ISO 3166-2 country code](https://en.wikipedia.org/wiki/ISO_3166-2#Current_codes) of the operators country
##### 3. Operator code

The operator code is vehicle type specific. The following IDs are used:

| Vehicle type | Region | Register                                                    |
|--------------|--------|-------------------------------------------------------------|
| plane        | global | [ICAO](https://en.wikipedia.org/wiki/List_of_airline_codes) |
| train        | europe | [VKM](https://www.era.europa.eu/domains/registers/vkm_en)   |

---

Combine these three values to `onboardapis.<type>.<country>.<operator>`.
This is the module that contains the API.

> **Hint**: You can also get the module path by looking at [Supported APIs](#supported-apis)
> / [Experimental APIs](#experimental-apis) and taking the three values from there.

## API scope

The API scope defines what information can be accessed through the API
and is a general indicator of the API's capabilities.  
The currently possible API scopes are:
- ``basic``: Only basic information is available such as connection status to the API.
- ``vehicle``: The API supplies information about the vehicle such as the train ID, line number, etc.
- ``geo``: The API supplies information about the current location, speed, etc. of the vehicle.
- ``journey-simple``: The API supplies simple journey information including the current station and the destination station.
- ``journey``: The API supplies detailed journey information including all the stations and possibly connecting services.
- ``full``: All of the above.
