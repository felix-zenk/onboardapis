from __future__ import annotations

import logging

from datetime import timedelta

from onboardapis.train.de.db import ICEPortal
from onboardapis.units import minutes, kilometers, kilometers_per_hour

logger = logging.getLogger(__name__)


def main():
    with ICEPortal() as train:
        logger.info('%s %s to %s', train.type, train.line_number, train.destination.name)
        if train.name:
            logger.info('Train name: %s', train.name)
        logger.info(
            'Next stop: %s at %s (in %.1f minutes, platform %s)',
            train.current_station.name,
            train.current_station.arrival.actual.strftime('%H:%M'),
            minutes(seconds=(train.current_station.arrival.actual - train.now).total_seconds()),
            train.current_station.platform.actual,
        )
        distance = train.calculate_distance(train.current_station)
        if distance < 1000:
            logger.info('Distance to train station: %d m', distance)
        else:
            logger.info('Distance to train station: %.2f km', kilometers(meters=distance))
        logger.info('Speed: %.1f km/h', kilometers_per_hour(meters_per_second=train.speed))
        if train.is_delayed:
            if train.delay < timedelta(minutes=5):
                logger.info(
                    'Travelling with a delay of %d seconds, because of: %s',
                    train.delay.total_seconds(),
                    ', '.join(train.delay_reasons)
                )
            else:
                logger.info(
                    'Travelling with a delay of %d minutes, because of: %s',
                    minutes(seconds=train.delay.total_seconds()),
                    ', '.join(train.delay_reasons)
                )
        logger.info('Passenger wagon class: %s', train.wagon_class)
        logger.info(
            'Journey: %s ... %s (%d stops)',
            train.origin.name,
            train.destination.name,
            len(train.stations)
        )
        if train.internet_access.is_enabled:
            logger.info('Internet access is enabled')
        else:
            logger.info('Internet access is disabled, enabling ...')
            train.internet_access.enable()
            logger.info('Done')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
