r"""
Progress Logging.

Scope: Logging and presenting progress messages and values.
"""


from controllables.core.components import Component

from ..systems import System


class ProgressLogger(Component[System]):
    r"""
    A logger that logs message and progress to a `tqdm.tqdm` progress bar.

    .. seealso:: https://tqdm.github.io
    """

    try: 
        import tqdm as _tqdm_
        import tqdm.auto as _tqdm_auto_
    except ModuleNotFoundError as e:
        from controllables.core.errors import OptionalModuleNotFoundError
        raise OptionalModuleNotFoundError.suggest(['tqdm']) from e

    def __init__(self, progbar_ref: _tqdm_.tqdm | None = None):
        r"""
        Initialize a new instance of :class:`ProgressLogger`.

        :param progbar_ref: Optional. The progress bar to log progress to.
            If not provided or ``None``, a new `tqdm.auto.tqdm` progress bar will be created.
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

    def __attach__(self, manager):
        super().__attach__(parent=manager)

        # TODO
        #self._events.__attach__(engine=self._engine)
        _events = self.parent.events
        
        def setup():
            nonlocal self, _events

            from ..events import Event
            progbar = (
                self._progbar_ref 
                if isinstance(self._progbar_ref, self._tqdm_.tqdm) else
                self._tqdm_auto_.tqdm(total=100.)
            )
            _events[Event.Ref('message', include_warmup=True)].on(
                lambda ctx, progbar=progbar: 
                    progbar.set_postfix_str(ctx.message)
            )
            _events[Event.Ref('progress', include_warmup=True)].on(
                lambda ctx, progbar=progbar: 
                    progbar.update(ctx.progress * progbar.total - progbar.n)
            )

        setup()

        return self


__all__ = [
    'ProgressLogger',
]