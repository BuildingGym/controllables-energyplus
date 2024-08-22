r"""
TODO 
"""


import builtins as _builtins_
import typing as _typing_
import operator as _operator_
import functools as _functools_


def IterableZipper(*iterables: _typing_.Iterable):
    return _builtins_.zip(*iterables)

# TODO ref https://stackoverflow.com/a/46328797
def MappingZipper(*mappings: _typing_.Mapping):
    keys_sets = _builtins_.map(_builtins_.set, mappings)
    common_keys = _functools_.reduce(_builtins_.set.intersection, keys_sets)
    for key in common_keys:
        yield (key, _builtins_.tuple(_builtins_.map(_operator_.itemgetter(key), mappings)))


__all__ = [
    'IterableZipper',
    'MappingZipper',
]