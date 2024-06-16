import builtins as _builtins_
import typing as _typing_
import collections as _collections_



class OrderedSetDict(
    _typing_.Generic[_typing_.TypeVar('T')],
    _collections_.OrderedDict,
):
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
    'OrderedSetDict',
    'CallableSet',
    'DefaultSet',
]





import collections as _collections_
import typing as _typing_

T = _typing_.TypeVar('T')

class OrderedSet(_typing_.Generic[T], _typing_.AbstractSet[T]):
    def __init__(self, iterable: _typing_.Iterable[T] = ()):
        self._data = _collections_.OrderedDict()
        self.update(iterable)
        
    def __contains__(self, element: T) -> bool:
        return element in self._data
    
    def __iter__(self) -> _typing_.Iterator[T]:
        return iter(self._data)
    
    def __len__(self) -> int:
        return len(self._data)
    
    def add(self, element: T) -> None:
        self._data[element] = None
    
    def discard(self, element: T) -> None:
        if element in self._data:
            del self._data[element]

    def remove(self, element: T) -> None:
        if element not in self._data:
            raise KeyError(element)
        del self._data[element]
    
    def update(self, *iterables: _typing_.Iterable[T]) -> None:
        for iterable in iterables:
            for element in iterable:
                self.add(element)
    
    def difference_update(self, *iterables: _typing_.Iterable[T]) -> None:
        for iterable in iterables:
            for element in iterable:
                self.discard(element)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({list(self._data)})"
    
    def __eq__(self, other: _typing_.Any) -> bool:
        if isinstance(other, OrderedSet):
            return self._data == other._data
        return False
    
    def __ne__(self, other: _typing_.Any) -> bool:
        return not self == other


__all__ = [
    'OrderedSet',
]
