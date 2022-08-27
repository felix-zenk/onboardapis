# onboardapis

[![PyPI-Versions](https://img.shields.io/pypi/pyversions/onboardapis)](https://pypi.org/project/onboardapis)
[![build](https://img.shields.io/github/workflow/status/felix-zenk/onboardapis/publish-to-pypi)](https://github.com/felix-zenk/onboardapis)
[![Documentation](https://img.shields.io/readthedocs/onboardapis)](https://onboardapis.readthedocs.io/en/latest/)
[![License](https://img.shields.io/github/license/felix-zenk/onboardapis)](https://github.com/felix-zenk/onboardapis/blob/main/LICENSE)

## Description

onboardapis is a Python package that provides wrappers for different on-board APIs.
What this means is that you can connect to the intranet of some vehicle by some operator 
and use the functionalities of this package to access meaningful data (such as the vehicles speed or position) 
if the operator provides a local API.

> **Note:** This package is still in development, so coverage across operators is not great yet.
> 
> For now the only vehicle type covered by this package is trains.

> **Note:** At the time this package supports the DB ICE Portal from germany and the ÖBB Railnet Regio from austria.
> 
> 

---

## Installation

Install the latest version of onboardapis from [PyPI](https://pypi.org/project/onboardapis) using [pip](https://pip.pypa.io/en/stable/installation/):

```shell
$ python -m pip install onboardapis
```

---

## Quickstart

To begin with development you will need to know a few things first:

* What vehicle type you want to use (e.g. train)
* Who operates the vehicle (e.g. Deutsche Bahn / DB)
* What country is the operator from (e.g. Germany)

With this information you can get the needed module from the package 
``onboardingapis.<vehicle-type>.<country>.<operator>`` 
and import the API wrapper class from it.

Let's say you want to use the on-board API of Deutsche Bahn trains in Germany.

```python
from onboardapis.trains.germany.db import ICEPortal
```

Every implementation of an API wrapper class is a subclass of the abstract class of its vehicle type
(here ``Train``) found in the vehicle package.

```python
from onboardapis.trains import Train
from onboardapis.trains.germany.db import ICEPortal

assert issubclass(ICEPortal, Train)
assert isinstance(ICEPortal(), Train)
```

The abstract base class defines common attributes that are used by all implementations.

For example, the ``Train`` class defines the attributes ``speed`` and ``delay`` alongside with the ``current station``
(the next station you will arrive at) and others.

```python
from onboardapis.trains.germany.db import ICEPortal
from onboardapis.utils.conversions import ms_to_kmh

train = ICEPortal()

print(
    "Travelling at", train.speed, "m/s",
    f"({ms_to_kmh(train.speed):.2f} km/h)",
    "with a delay of", train.delay, "seconds"
)

print(
    "Next stop:", train.current_station.name, 
    "at", train.current_station.arrival.actual.strftime("%H:%M")
)

print(
    f"Distance to {train.current_station.name}:",
    f"{train.calculate_distance(train.current_station):.1f} km"
)
```
And there you go!
You can read more information about available attributes in the [trains documentation](https://onboardapis.readthedocs.io/en/latest/source/onboardapis.trains.html).

---

## Documentation
[![Documentation](https://img.shields.io/readthedocs/onboardapis)](https://onboardapis.readthedocs.io/en/latest/)

[ReadTheDocs](https://onboardapis.readthedocs.io/en/latest/)
