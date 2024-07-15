r"""
Message Logging.

Scope: Logging and presenting messages.
"""

from .. import base as _base_


# TODO mv adapters/energyplus
class MessageLogger(_base_.Addon):
    r"""
    A logger that logs messages to a `logging.Logger`.

    ..seealso:: https://docs.python.org/3/library/logging.html
    """

    import logging as _logging_

    def __init__(self, logger_ref: _logging_.Logger | str | None = None):
        r"""
        Initialize a new instance of :class:`MessageLogger`.

        :param logger_ref: The logger or the name of the logger to log messages to.
            If not provided or `None`, a new logger with the name of the attached engine will be created.
        """

        super().__init__()
        self._logger_ref = logger_ref
        # TODO
        #self._events = _components_.events.EventManager()

        #super().__attach__.on('call:post', ...)

    def __attach__(self, engine):
        super().__attach__(manager=engine)

        # TODO
        #self._events.__attach__(engine=self._engine)
        self._events = self._manager.events

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
                .on('message', lambda ctx, logger=logger: 
                    logger.info(ctx.message))

        setup()

        return self


__all__ = [
    'MessageLogger',
]