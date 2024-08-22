import typing as _typing_
import collections as _collections_


# TODO https://stackoverflow.com/questions/1653970/does-python-have-an-ordered-set
class OrderedSet(
    _typing_.AbstractSet[_T := _typing_.TypeVar('_T')],
    _typing_.Generic[_T], 
):
    def __init__(self, iterable: _typing_.Iterable[_T] = ()):
        self._data = _collections_.OrderedDict()
        self.update(iterable)
        
    def __contains__(self, element: _T) -> bool:
        return element in self._data
    
    def __iter__(self) -> _typing_.Iterator[_T]:
        return iter(self._data)
    
    def __len__(self) -> int:
        return len(self._data)
    
    def add(self, element: _T) -> None:
        self._data[element] = None
    
    def discard(self, element: _T) -> None:
        if element in self._data:
            del self._data[element]

    def remove(self, element: _T) -> None:
        if element not in self._data:
            raise KeyError(element)
        del self._data[element]
    
    def update(self, *iterables: _typing_.Iterable[_T]) -> None:
        for iterable in iterables:
            for element in iterable:
                self.add(element)
    
    def difference_update(self, *iterables: _typing_.Iterable[_T]) -> None:
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
