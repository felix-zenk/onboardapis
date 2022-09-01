"""
Exceptions for the onboardapis package.
"""


class OnboardException(Exception):
    """
    Base exception class for on-board exceptions.
    """

    __slots__ = []


class APIConnectionError(OnboardException, ConnectionError):
    """
    Exception raised when an API connection error occurs.
    """

    __slots__ = []


class InitialConnectionError(APIConnectionError):
    """
    Exception raised only when the first try to connect to an API fails.
    """

    __slots__ = []

    def __init__(self, message: str = "Unable to connect to the API, are you connected to the on-board WI-FI?", *args):
        super(InitialConnectionError, self).__init__(message, *args)


class DataInvalidError(APIConnectionError):
    """
    Error raised when an API sends a response that could not be parsed due to a formatting error
    or when the data is missing
    """

    __slots__ = []

    def __init__(self, message: str = "The API returned an invalid response", *args):
        super(DataInvalidError, self).__init__(message, *args)
