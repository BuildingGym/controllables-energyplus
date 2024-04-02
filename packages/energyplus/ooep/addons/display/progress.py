from .. import base as _base_


class ProgressProvider(_base_.Addon):
    try: 
        import tqdm as _tqdm_
        import tqdm.auto
    except ImportError as e:
        raise _base_.OptionalImportError(['tqdm']) from e

    def __init__(self, progbar_ref: _tqdm_.tqdm | None = None):
        super().__init__()
        self._progbar_ref = progbar_ref

    def __attach__(self, engine):
        super().__attach__(engine=engine)

        def setup():
            nonlocal self            
            progbar = (
                self._progbar_ref 
                if isinstance(self._progbar_ref, self._tqdm_.tqdm) else
                self._tqdm_.auto.tqdm(total=100)
            )
            self._engine._events \
                .on('message', lambda event, progbar=progbar: 
                    progbar.set_postfix_str(event.message)) \
                .on('progress', lambda event, progbar=progbar: 
                    progbar.update(event.progress * progbar.total - progbar.n))

        setup()

        return self


__all__ = [
    ProgressProvider,
]