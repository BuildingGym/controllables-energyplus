r"""
Exceptions
"""


class TemporaryUnavailableError(Exception):
    r"""
    Exception raised for resources that are temporarily unavailable.

    In the scope of this package, such exception often implies that 
    a variable or an entity does not currently exist but may become
    available in the future, though not guaranteed.
    """

    pass


__all__ = [
    'TemporaryUnavailableError',
]