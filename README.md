onboardapis
===

[![Python versions](https://img.shields.io/pypi/pyversions/onboardapis)](https://pypi.org/project/onboardapis)
[![PyPI version](https://badge.fury.io/py/onboardapis.svg)](https://pypi.org/project/onboardapis)
[![License](https://img.shields.io/github/license/felix-zenk/onboardapis)](https://github.com/felix-zenk/onboardapis/blob/main/LICENSE)  
[![Build package](https://github.com/felix-zenk/onboardapis/actions/workflows/build.yml/badge.svg)](https://github.com/felix-zenk/onboardapis/actions/workflows/build.yml)
[![Deploy documentation](https://github.com/felix-zenk/onboardapis/actions/workflows/docs.yml/badge.svg)](https://github.com/felix-zenk/onboardapis/actions/workflows/docs.yml)

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

[![Version](https://img.shields.io/pypi/v/onboardapis?label=%20)](https://pypi.org/project/onboardapis)

or the latest prerelease version of onboardapis
from [PyPI](https://pypi.org/project/onboardapis/2.0.0rc3/)
using [pip](https://pip.pypa.io/en/stable/installation/):

```shell
$ python -m pip install --pre onboardapis
```

[![Version](https://img.shields.io/badge/v2.0.0rc4-%20?color=1081c2)](https://pypi.org/project/onboardapis/2.0.0rc4/)

---

Install the latest development version of onboardapis
from [GitHub](https://github.com/felix-zenk/onboardapis)
using [pip](https://pip.pypa.io/en/stable/installation/):

```shell
$ python -m pip install git+https://github.com/felix-zenk/onboardapis.git
```

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
from onboardapis.units import kilometers, kilometers_per_hour

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
    f"({kilometers_per_hour(meters_per_second=train.speed):.2f} km/h)",
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

Mostly stable APIs.

| API                   | [API scope](#api-scope)                    | Type  | Country      | Operator                                |
|-----------------------|--------------------------------------------|-------|--------------|-----------------------------------------|
| RailnetRegio          | basic, geo                                 | train | at (Austria) | obb (Österreichische Bundesbahnen)      |
| ICEPortal             | *internet-access*\*, vehicle, geo, journey | train | de (Germany) | db (Deutsche Bahn / DB AG)              |
| FlixTainment          | basic, geo                                 | train | de (Germany) | flix (Flix Train GmbH)                  |
| MetronomCaptivePortal | internet-access                            | train | de (Germany) | me (metronom Eisenbahngesellschaft mbH) |

> **Notes**:
> - \* Not supported yet.

## Experimental APIs

APIs that are considered experimental and may change in the future.

| API                    | [API scope](#api-scope)            | Type  | Country      | Operator                     |
|------------------------|------------------------------------|-------|--------------|------------------------------|
| PortalINOUI            | basic, vehicle, geo, journey       | train | fr (France)  | sncf (SNCF Voyageurs)        |
| RegioGuide / ZugPortal | basic, vehicle, geo, journey       | train | de (Germany) | db (Deutsche Bahn / DB AG)   |
| PortaleRegionale       | basic, basic-journey               | train | it (Italy)   | ti (Trenitalia S.p.A.)       |
| SBahnHannover          | *internet-access*\*, basic-journey | train | de (Germany) | tdh (Transdev Hannover GmbH) |

> **Notes**:
> - \* Not supported yet.

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
Scopes can be combined.  
The currently possible API scopes are:
- ``basic`` / ``internet-access``: basic information is available such as connection status to the API. / The internet access can be enabled and disabled.
- ``vehicle``: The API supplies information about the vehicle such as the train ID, line number, etc.
- ``geo``: The API supplies information about the current location, speed, etc. of the vehicle.
- ``basic-journey`` / ``journey``: The API supplies basic journey information including the current station and the destination station. / The API supplies detailed journey information including all the stations and possibly connecting services.
