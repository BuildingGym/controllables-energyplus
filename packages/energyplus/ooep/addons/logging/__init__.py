from __future__ import annotations

from .. import base as _base_
from ... import (
    components as _components_,
)


class LogProvider(_base_.Addon):
    import logging as _logging_

    def __init__(self, logger_ref: _logging_.Logger | str | None = None):
        super().__init__()
        self._logger_ref = logger_ref
        # TODO
        #self._events = _components_.events.EventManager()

    def __attach__(self, engine):
        super().__attach__(engine=engine)

        # TODO
        #self._events.__attach__(engine=self._engine)
        self._events = self._engine.events

        def setup():
            nonlocal self
            logger = (
                self._logger_ref 
                if isinstance(self._logger_ref, self._logging_.Logger) else
                self._logging_.getLogger(
                    name=
                        self._logger_ref 
                        if self._logger_ref is not None else 
                        str(engine)
                )
            )
            self._events \
                .on('message', lambda event, logger=logger: 
                    logger.info(event.message))

        setup()

        return self


__all__ = [
    'LogProvider',
]