import sys as _sys_
import typing as _typing_


class OptionalImportError(ImportError):
    @classmethod
    def suggest(cls, package_names: _typing_.Collection[str]):
        return cls(
            'Missing optional dependency(ies)/module(s), run: '
            f'''`{_sys_.executable} -m pip install {
                str.join(' ', (f'"{s}"' for s in package_names))}`'''
        )

    
from ... import (
    components as _components_,
)

from ...specs.components import (
    BaseComponent,
)

Addon = BaseComponent[_components_.world.World]

#class Addon(Component):
#    _engine: _components_.worlds.World


__all__ = [
    'OptionalImportError',
    'BaseComponent',
    'Addon',
]
