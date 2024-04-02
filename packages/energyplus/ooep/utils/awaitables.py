import typing as _typing_
import functools as _functools_
import asyncio as _asyncio_


class asyncify:
    """
    TODO doc
    Decorator to convert a synchronous method to asynchronous
    by running it in a separate thread.
    """

    def __init__(
        self, 
        loop: _asyncio_.AbstractEventLoop = None,
        executor: _typing_.Any = None,
    ):
        self._loop = loop
        self._executor = executor

    def __call__(self, func):
        @_functools_.wraps(func)
        async def async_func(*args, **kwargs):
            nonlocal self
            loop = (self._loop if self._loop is not None 
                    else _asyncio_.get_event_loop())
            return await loop.run_in_executor(
                executor=self._executor, 
                func=_functools_.partial(func, *args, **kwargs),
            )
        return async_func


__all__ = [
    asyncify,
]