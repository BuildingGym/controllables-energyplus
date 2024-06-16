r"""
Progress Logging.

Scope: Logging and presenting progress messages and values.
"""

from .. import base as _base_
from ... import (
    components as _components_,
)


class ProgressLogger(_base_.Addon):
    r"""
    A logger that logs message and progress to a `tqdm.tqdm` progress bar.

    ..seealso:: https://tqdm.github.io/
    """

    try: 
        import tqdm as _tqdm_
        import tqdm.auto
    except ImportError as e:
        raise _base_.OptionalImportError.suggest(['tqdm']) from e

    def __init__(self, progbar_ref: _tqdm_.tqdm | None = None):
        r"""
        Initialize a new instance of :class:`ProgressLogger`.

        :param progbar_ref: Optional. The progress bar to log progress to.
            If not provided or `None`, a new `tqdm.auto.tqdm` progress bar will be created.
        """

        super().__init__()
        self._progbar_ref = progbar_ref
        # TODO
        #self._progbar_instance = None
        # TODO
        #self._events = _components_.events.EventManager()

    # TODO
    # TODO cached property
    def _progbar_instance(self):
        raise NotImplementedError

    def __attach__(self, engine):
        super().__attach__(engine=engine)

        # TODO
        #self._events.__attach__(engine=self._engine)
        _events = self._engine.events
        
        def setup():
            nonlocal self, _events
            progbar = (
                self._progbar_ref 
                if isinstance(self._progbar_ref, self._tqdm_.tqdm) else
                self._tqdm_.auto.tqdm(total=100)
            )
            _events \
                .on('message', lambda event, progbar=progbar: 
                    progbar.set_postfix_str(event.message)) \
                .on('progress', lambda event, progbar=progbar: 
                    progbar.update(event.progress * progbar.total - progbar.n))

        setup()

        return self


__all__ = [
    'ProgressLogger',
]