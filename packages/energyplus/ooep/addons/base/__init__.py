import sys as _sys_
import typing as _typing_


class OptionalImportError(ImportError):
    @classmethod
    def suggest(cls, package_names: _typing_.Collection[str]):
        return cls(
            'Missing optional dependency(ies)/module(s): '
            f'''{str.join(', ', package_names)}. '''
            f'''Install them through {_sys_.executable} to use this feature.'''
        )
    
from ... import (
    components as _components_,
    engines as _engines_,
)


class Addon(_components_.base.Component):
    _engine: '_engines_.simulators.Simulator'


__all__ = [
    'OptionalImportError',
    'Addon',
]
