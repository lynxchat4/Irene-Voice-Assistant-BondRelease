import logging
from collections import Iterable

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
