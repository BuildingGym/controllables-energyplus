r"""
Built-in attributes.

"""


class numeric:
    r"""
    Numeric attributes.

    .. seealso:: https://docs.python.org/3/reference/datamodel.html#emulating-numeric-types
    """

    BINARY = (
        '__add__',
        '__sub__',
        '__mul__',
        '__matmul__',
        '__truediv__',
        '__floordiv__',
        '__mod__',
        '__divmod__',
        '__pow__',
        '__lshift__',
        '__rshift__',
        '__and__',
        '__xor__',
        '__or__',
    )
    r"""Binary arithmetic attributes."""

    RBINARY = (
        '__radd__',
        '__rsub__',
        '__rmul__',
        '__rmatmul__',
        '__rtruediv__',
        '__rfloordiv__',
        '__rmod__',
        '__rdivmod__',
        '__rpow__',
        '__rlshift__',
        '__rrshift__',
        '__rand__',
        '__rxor__',
        '__ror__',
    )
    r"""Binary arithmetic attributes, reflected."""

    IBINARY = (
        '__iadd__',
        '__isub__',
        '__imul__',
        '__imatmul__',
        '__itruediv__',
        '__ifloordiv__',
        '__imod__',
        '__ipow__',
        '__ilshift__',
        '__irshift__',
        '__iand__',
        '__ixor__',
        '__ior__',
    )
    r"""Binary arithmetic attributes, in-place."""

    UNARY = (
        '__neg__',
        '__pos__',
        '__abs__',
        '__invert__',
    )
    r"""Unary arithmetic attributes."""

    CAST = (
        '__complex__',
        '__int__',
        '__float__',        
    )
    r"""Type conversion."""

    INDEX = (
        '__index__',
    )
    r"""Index conversion."""

    TRUNC = (
        '__round__',
        '__trunc__',
        '__floor__',
        '__ceil__',
    )
    r"""Truncation."""


__all__ = [
    'numeric',
]