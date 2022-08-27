.. _documentation:

The package
===========

Structure
*********

   The package is structured into an abstract base, found in the ``onboardapis.<vehicle_type>`` subpackages,
   and the concrete implementations found in the ``onboardapis.<vehicle_type>.<country>`` subpackages.

   So for example, the ``onboardapis.trains.germany`` package
   contains the concrete implementations train service providers located in germany.
   Each provider has its own module and each on-board API of this provider has a class in that module.

   If you want to interact with the ICE-Portal from DB in its ICE trains you can access the class ICEPortal in the
   ``onboardapis.trains.germany.db`` module:

   .. code-block:: python

       from onboardapis.trains.germany.db import ICEPortal


Module Overview
***************

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   source/modules
   source/onboardapis
   source/onboardapis.trains
   source/onboardapis.trains.austria
   source/onboardapis.trains.germany
   source/onboardapis.utils
