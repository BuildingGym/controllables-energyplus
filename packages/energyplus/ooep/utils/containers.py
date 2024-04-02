import builtins as _builtins_
import typing as _typing_
import collections as _collections_

class OrderedSetDict(_collections_.OrderedDict):
    def add(self, v):
        self[v] = v

    def update(self, *s: _typing_.Iterable):
        for it in s:
            for el in it:
                self.add(el)

    def remove(self, v):
        return self.pop(v)
    
    def difference_update(self, *s: _typing_.Iterable):
        for it in s:
            for el in it:
                self.remove(el)

# TODO
# TODO NOTE data format {<callable>: <callable>} {<key>: <callable>}
class CallableSet(OrderedSetDict):
    def __call__(self, *args, **kwargs):
        return _collections_.OrderedDict({
            key: f.__call__(*args, **kwargs)
                for key, f in self.items()
        })

# TODO
class DefaultSet(_builtins_.set):
    def __init__(self, default_factory):
        self._default_factory = default_factory

    def add(self, *args, **kwargs):
        return super().add(self._default_factory(*args, **kwargs))


__all__ = [
    OrderedSetDict,
    CallableSet,
    DefaultSet,
]
