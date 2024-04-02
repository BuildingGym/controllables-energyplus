import logging as _logging_

from . import base as _base_

class Logger(_logging_.Logger, _base_.Component):
    # TODO
    def attach(self, supervisor):
        super().attach(supervisor=supervisor)
        self._supervisor._events.on(
            'message', lambda event: self.info(event.message)
        )
        return self

__all__ = [
    Logger,
]