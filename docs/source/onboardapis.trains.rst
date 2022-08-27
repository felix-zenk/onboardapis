.. _trains_documentation:

onboardapis.trains package
==========================

The ``Train`` class is the abstract base class for all trains. It provides

* id: The train's id
* type: The train's type
* number: The train's line number
* stations: A list of all stations on the journey
* origin: The first station on the journey
* current_station: The station the train is currently at or visits the next
* destination: The last station on the journey
* speed: The train's current speed (m/s)
* distance: The distance the train has travelled from the start (m)
* position: The geographical position of the train
* delay: The current delay of the train (s)
* now(): The current time provided by the train
* calculate_distance(station): Calculate the distance from the train's current position to the given station
* init(): Initialize the train

Stations are represented by the ``Station`` class.
Each station has the following attributes:

* id: The station's id
* name: The name of the station
* platform: The platform the train will arrive at (ScheduledEvent[str])
* arrival: The time the train arrives at the station (ScheduledEvent[datetime])
* departure: The time the train departs from the station (ScheduledEvent[datetime])
* connections: A list of all ``ConnectingTrain`` departing from this station
* distance: The distance from the start of the journey to this station (m)
* position: The geographical position of the station
* calculate_distance(station|tuple|int|float): Calculate the distance from the station to another station or a position

The ``platform``, ``arrival`` and ``departure`` attributes are ``ScheduledEvents``.
They each contain the attributes ``scheduled`` and ``actual``.

Subpackages
-----------

.. toctree::
   :maxdepth: 4

   onboardapis.trains.austria
   onboardapis.trains.germany

Submodules
----------

onboardapis.trains.extensions module
------------------------------------

.. automodule:: onboardapis.trains.extensions
   :members:
   :undoc-members:
   :show-inheritance:

onboardapis.trains.selector module
----------------------------------

.. automodule:: onboardapis.trains.selector
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: onboardapis.trains
   :members:
   :undoc-members:
   :show-inheritance:
