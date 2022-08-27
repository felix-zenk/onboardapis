.. _getting-started:

Getting started
===============

To begin with development you will need to know a few things first:

* What vehicle type you want to use (e.g. train)
* Who operates the vehicle (e.g. Deutsche Bahn / DB)
* What country is the operator from (e.g. Germany)

With this information you can get the needed module from the package
``onboardingapis.<vehicle-type>.<country>.<operator>``
and import the API wrapper class from it.

Let's say you want to use the on-board API of Deutsche Bahn trains in Germany, which is called the ICE Portal.

.. code-block:: python

    from onboardapis.trains.germany.db import ICEPortal


Every implementation of an API wrapper class is a subclass of the abstract class of its vehicle type
(here ``Train``) found in the vehicle package.

.. code-block:: python

    from onboardapis.trains import Train
    from onboardapis.trains.germany.db import ICEPortal

    assert issubclass(ICEPortal, Train)
    assert isinstance(ICEPortal(), Train)


The abstract base class defines common attributes that are used by all implementations.

For example, the ``Train`` class defines the attributes ``speed`` and ``delay`` alongside with the ``current station``
(the next station you will arrive at) and others.

.. code-block:: python

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


And there you go!
You can read more information about available attributes in the
:ref:`trains_documentation`.



.. toctree::
   :maxdepth: 2
   :caption: Contents:
