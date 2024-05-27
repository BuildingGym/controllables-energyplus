r"""
Message Logging.

Scope: Logging and presenting messages.
"""

from .. import base as _base_
from ... import (
    components as _components_,
    exceptions as _exceptions_,
)


class MessageLogger(_base_.Addon):
    r"""
    A logger that logs messages to a `logging.Logger`.

    ..seealso:: https://docs.python.org/3/library/logging.html
    """

    import logging as _logging_

    def __init__(self, logger_ref: _logging_.Logger | str | None = None):
        r"""
        Initializes a new instance of :class:`MessageLogger`.

        :param logger_ref: The logger or the name of the logger to log messages to.
            If not provided or `None`, a new logger will be created with the name of the engine.
        """

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

# TODO deprecate
LogProvider = MessageLogger


__all__ = [
    'MessageLogger',
]