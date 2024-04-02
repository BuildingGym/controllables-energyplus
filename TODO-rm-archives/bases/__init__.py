import abc as _abc_
import typing as _typing_


class BaseComponentSupervisor(_abc_.ABC):
    pass

class BaseComponent(_abc_.ABC):
    def __init__(self):
        self._supervisor = None

    def attach(self, supervisor: BaseComponentSupervisor) -> _typing_.Self:
        self._supervisor = supervisor
        return self

    @property
    def supervisor(self) -> BaseComponentSupervisor:
        if self._supervisor is None:
            raise ValueError('No supervisor. Call `attach`.')
        return self._supervisor

# TODO rm
'''
class BaseSpecs(_abc_.ABC):
    # TODO NOTE this constructs an object according to `BaseSpecs`
    @classmethod
    def __build__(cls, specs: 'BaseSpecs') -> _typing_.Any:
        raise NotImplementedError



class BaseVariable(BaseComponent, _abc_.ABC):
    class Specs(BaseSpecs, _abc_.ABC):
        @classmethod
        def __build__(cls, specs: 'BaseSpecs') -> 'BaseVariable':
            raise NotImplementedError

    # TODO
    def __init__(
        self,
        specs: BaseSpecs,
    ):
        super().__init__()
        self._specs = specs

    @property
    def specs(self):
        return self._specs
        
    @property
    def value(self):
        ...

class BaseControlVariable(BaseVariable, _abc_.ABC):
    @BaseVariable.value.setter
    def value(self, o: _typing_.Any):
        ...

'''
