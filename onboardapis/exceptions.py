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


class DataInvalidError(APIConnectionError):
    """
    Error raised when an API sends a response that could not be parsed due to a formatting error
    or when the data is missing
    """

    __slots__ = []

    def __init__(self, message: str = "The API returned an invalid response"):
        super(DataInvalidError, self).__init__(message)
