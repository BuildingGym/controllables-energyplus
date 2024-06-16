import typing as _typing_
import functools as _functools_
import asyncio as _asyncio_


class asyncify:
    r"""
    Decorator to convert a synchronous method to asynchronous
    by running it in a separate thread.

    Example usage:

    .. code-block:: python

        import asyncio

        @asyncify()
        def blocking_function(x):
            # Simulate a blocking operation
            time.sleep(x)
            return x

        async def main():
            result = await blocking_function(1)
            print(result)

        asyncio.run(main())

    In this example, `blocking_function` is wrapped by `asyncify`, 
    enabling it to be `await`-ed in an asynchronous environment.
    """

    def __init__(
        self, 
        loop: _asyncio_.AbstractEventLoop = None,
        executor: _typing_.Any = None,
    ):
        r"""
        Initializes the `asyncify` decorator with an optional event loop and executor.

        :param loop: 
            The event loop where the asynchronous execution will be scheduled. If not provided, the
            default event loop for the current thread is used. This parameter allows the user to specify
            a different event loop if needed, which is useful in applications running multiple event loops.
        :param executor: 
            The executor in which the synchronous function will be run. If not provided, the default
            executor of the event loop is used, which is usually a thread pool executor. This allows
            for customization of how the function is executed, for example, by using a process pool
            executor for CPU-bound tasks.
        """

        self._loop = loop
        self._executor = executor

    def __call__(self, func: callable):
        r"""
        Wraps a function to make it asynchronous by running it in a separate thread.

        This method is called when `asyncify` is used as a decorator. It wraps the provided synchronous function
        in an asynchronous function that, when called, schedules the synchronous function to be executed in a
        separate thread using the event loop's executor.

        :param func: The synchronous function to be converted into an asynchronous function.
        :return: An asynchronous version of the `func` which, when called, returns a future representing the
                 execution of `func` in a separate thread.
        """

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
    'asyncify',
]