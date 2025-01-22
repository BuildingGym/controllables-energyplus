
import controllables.core.callables as _mod_
import doctest as _doctest_


class TestDocs:
    def test_doctests(self):
        _doctest_.testmod(_mod_, raise_on_error=True, verbose=True)
