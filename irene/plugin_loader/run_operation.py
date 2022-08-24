import logging
from collections import Iterable
from functools import partial
from threading import Thread
from typing import Callable, Any, Collection

from irene.plugin_loader.plugins_abc import OperationStep


def call_all(steps: Iterable[OperationStep], *args, **kwargs):
    for step in steps:
        step.step(*args, **kwargs)


def call_all_failsafe(steps: Iterable[OperationStep], *args, **kwargs):
    for step in steps:
        try:
            step.step(*args, **kwargs)
        except Exception:
            logging.exception("Ошибка при выполнении шага %s", step)


def call_until_first_result(steps: Iterable[OperationStep], *args, **kwargs):
    for step in steps:
        result = step.step(*args, **kwargs)

        if result is not None:
            return result


def call_all_as_wrappers(steps: Iterable[OperationStep], initial: Any, *args, **kwargs) -> Any:
    def _call_wrapper(s: Collection[OperationStep], prev: Any):
        if len(s) == 0:
            return prev

        step, *rest = s

        return step.step(prev, partial(_call_wrapper, rest), *args, **kwargs)

    return _call_wrapper(tuple(steps), initial)


def call_all_parallel(steps: Iterable[OperationStep], *args, **kwargs):
    threads: list[Thread] = []

    def start_thread(callback: Callable, name: str):
        thread = Thread(
            name=name,
            daemon=True,
            target=callback,
            args=args, kwargs=kwargs,
        )
        thread.start()
        threads.append(thread)

    for step in steps:
        if callable(step.step):
            start_thread(step.step, str(step))
        else:
            raise TypeError(f"Неподдерживаемый тип шага {step}: {type(step.step)}")

    for t in threads:
        # простой вызов join() игнорирует KeyboardInterrupt
        while t.is_alive():
            t.join(1.0)
