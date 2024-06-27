"""
Exceptions for the onboardapis package.
"""
from __future__ import annotations

from restfly.errors import APIError


class OnboardException(Exception):
    """Base exception class for on-board exceptions."""

    __slots__ = ()


class APIConnectionError(OnboardException, ConnectionError):
    """Exception raised when an API connection error occurs."""

    __slots__ = ()


class InitialConnectionError(APIConnectionError):
    """Exception raised only when the first try to connect to an API fails."""

    __slots__ = ()

    def __init__(self, message: str = "Unable to connect to the API, are you connected to the on-board Wi-Fi?", *args):
        super(InitialConnectionError, self).__init__(message, *args)


class DataInvalidError(APIConnectionError):
    """Error raised when an API sends a response that could not be parsed
    due to a formatting error or when the data is missing."""

    __slots__ = ()

    def __init__(self, message: str = "The API returned an invalid response", *args):
        super(DataInvalidError, self).__init__(message, *args)


class APIFeatureMissingError(APIConnectionError, APIError):
    """Error raised when an API could support a feature,
    but the actual implementation onboard this vehicle does not support this feature."""

    __slots__ = ()

    def __init__(self, resp, message: str = None, **kwargs):
        if not message:
            message = "The requested feature (%s) is not supported by this API" % resp.url
        APIConnectionError.__init__(self, message)
        APIError.__init__(self, resp, **kwargs)
        self.set_retryable(value=False)
