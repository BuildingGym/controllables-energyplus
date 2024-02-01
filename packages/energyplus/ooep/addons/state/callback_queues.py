import queue

import dataclasses
import typing


class CallbackQueue:
    @dataclasses.dataclass
    class Task:
        func: typing.Callable | None = None
        result: typing.Any = None

    def __init__(self, maxsize=1):
        self.base = queue.Queue(maxsize=maxsize)

    def __call__(self, *args, **kwargs):
        task: self.Task = self.base.get()
        if task.func is not None:
            task.result = task.func(*args, **kwargs)
        self.base.task_done()

    def call(self, func: typing.Callable | None = None):
        task = self.Task(func=func)
        self.base.put(task)
        self.base.join()
        return task.result

class CloseableCallbackQueue(CallbackQueue):
    class Closed(Exception):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = False

    def __call__(self, *args, **kwargs):
        if self.closed:
            raise self.Closed()
        return super().__call__(*args, **kwargs)
    
    def call(self, func: typing.Callable):
        if self.closed:
            raise self.Closed()
        return super().call(func)
    
    def open(self):
        self.closed = False

    def close(self):
        self.closed = True
        # NOTE ref https://stackoverflow.com/a/18873213
        while not self.base.empty():
            try: self.base.get(block=False)
            except queue.Empty: continue
            self.base.task_done()


__all__ = [
    CallbackQueue,
    CloseableCallbackQueue,
]