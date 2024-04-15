r"""
Exceptions
"""

class TemporaryUnavailableError(Exception):
    r"""
    Exception raised for resources that are temporarily unavailable.

    In the scope of this package, such exception often implies that 
    a variable or an entity does not currently exist but may become
    available in the future, though not guaranteed.

    This exception is meant to be caught and handled by the calling code, 
    often to implement retry logic or to inform the user about 
    the temporary unavailability.
    """

    pass

__all__ = [
    'TemporaryUnavailableError',
]