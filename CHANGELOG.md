# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Changelog

### Changed

- Use YAML based resource files
- RegioGuideInternetAccessAPI autodetect internet access provider
- Renamed `UnwiredMapMixin` to `UnwiredPositionMixin`

### Removed

- Deprecated method `RailnetRegio.combined`

## [2.0.0] - 2023-06-27

### Added

- `MetronomCaptivePortal` class
- `PortalINOUI` class
- `PortaleRegionale` class
- `SBahnHannover` class
- `APIFeatureMissingError`
- Mixin classes for features of vehicles

### Fixed

- Type hints

### Changed

- Renamed `ZugPortal` to `RegioGuide`
- Updated dependencies
- Package structure
- Convert all methods of `Train` except `init`, `shutdown` to properties

### Removed

- `ZugPortal` class
- Mixin classes for incomplete vehicles

## [1.3.2] - 2024-02-27

### Fixed

- `DataInvalidError` with null unsafe return ([#2](https://github.com/felix-zenk/onboardapis/issues/2))
- `RailnetRegio.position` altitude, heading by [@Totto16](https://github.com/Totto16)

## [1.3.1] - 2022-10-11

### Fixed

- MRO for `FlixTainment`

## [1.3.0] - 2022-10-11

### Added

- `NotImplementedInAPIError` for functionalities not covered by the providers API
- `IncompleteVehicleMixin` and `IncompleteTrainMixin` mixin classes
- `DummyDataConnector` class that does nothing
- `FlixTainment` class providing support for FlixTrains

## [1.2.3] - 2022-09-18

### Fixed

- TLS can't be disabled for a whole `DataConnector` anymore
- Reorganized and optimized parts of the backend code

## [1.2.2] - 2022-09-08

### Fixed

- Type hints
- `JSONDataConnector` adds an application/json header
- `Station.connections` for `ICEPortal`

## [1.2.1] - 2022-09-07

### Fixed

- TypeError in `Station.calculate_distance()`
- Generation of `ICEPortal.all_delay_reasons()`


## [1.2.0] - 2022-09-05

### Added

- `Vehicle` base class
- `Position` class
- `ICEPortal.name` property that returns the baptismal name of the train

### Fixed

- Calculation of `ICEPortal.distance`
- Resolved an error in `coordinates_dms_to_decimal()`

## [1.1.0] - 2022-09-02

### Added

- `Train.connected` property
- `Train.shutdown()` method
- `Train` context manager which calls `Train.init()` on enter and `Train.shutdown()` on exit
- `InitialConnectionError` class to better indicate whether the connection to the API is lost or can't be established
- conversion functions for coordinates

### Fixed

- An issue where `ICEPortal` fails to generate `ICEPortal.stations`

## [1.0.0] - 2022-08-27

### Added

- `RailnetRegio` class
- `ICEPortal` class

[unreleased]: https://github.com/felix-zenk/onboardapis/compare/2.0.0...HEAD
[2.0.0]: https://github.com/felix-zenk/onboardapis/compare/v1.3.2...2.0.0
[1.3.2]: https://github.com/felix-zenk/onboardapis/compare/1.3.1...v1.3.2
[1.3.1]: https://github.com/felix-zenk/onboardapis/compare/1.3.0...1.3.1
[1.3.0]: https://github.com/felix-zenk/onboardapis/compare/1.2.3...1.3.0
[1.2.3]: https://github.com/felix-zenk/onboardapis/compare/1.2.2...1.2.3
[1.2.2]: https://github.com/felix-zenk/onboardapis/compare/1.2.1...1.2.2
[1.2.1]: https://github.com/felix-zenk/onboardapis/compare/1.2.0...1.2.1
[1.2.0]: https://github.com/felix-zenk/onboardapis/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/felix-zenk/onboardapis/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/felix-zenk/onboardapis/releases/tag/1.0.0
