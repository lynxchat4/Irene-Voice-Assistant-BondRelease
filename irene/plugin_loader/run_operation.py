"""
Содержит вспомогательные функции для выполнения операций (см. документацию к модулю ``irene.plugins.abc``).
"""

import asyncio
from functools import partial
from typing import Any, Collection, Iterable

from irene.plugin_loader.abc import OperationStep


def call_all(steps: Iterable[OperationStep], *args, **kwargs):
    """
    Выполняет все шаги операции последовательно.

    Args:
        steps:
            шаги операции
        *args:
            позиционные аргументы для вызова шагов
        **kwargs:
            именованные аргументы для вызова шагов
    Raises:
        TypeError - если один из шагов не является функцией
    """
    for step in steps:
        if not callable(step.step):
            raise TypeError(f"Шаг {step} не является функцией")

        step.step(*args, **kwargs)


def call_until_first_result(steps: Iterable[OperationStep], *args, **kwargs):
    """
    Вызывает все шаги по-очереди пока какой-нибудь из них не вернёт результат (не None).

    Args:
        steps:
            шаги операции
        *args:
            позиционные аргументы для вызова шагов
        **kwargs:
            именованные аргументы для вызова шагов

    Returns:
        результат, возвращённый одним из шагов операции или None если ни один из шагов не вернул значение
    Raises:
        TypeError - если какой-то из шагов не является функцией
    """
    for step in steps:
        if not callable(step.step):
            raise TypeError(f"Шаг {step} не является функцией")

        result = step.step(*args, **kwargs)

        if result is not None:
            return result


def call_all_as_wrappers(steps: Iterable[OperationStep], initial: Any, *args, **kwargs) -> Any:
    """
    Вызывает все шаги, предоставляя возможность каждому шагу получать доступ как к промежуточным результатам выполнения
    предыдущих шагов, так и к результату выполнения всех последующих.

    Позволяет гибко создавать сложные объекты, совмещая и оборачивая объекты, созданные другими шагами.

    Первые два позиционных аргумента функции шага имеют особое значение:

    - первый аргумент - функция, вызов которой выполняет последующие шаги.
      Первый аргумент этой функции будет передан следующему шагу вторым аргументом, так же будут переданы и все
      позиционные и именованные аргументы.

    - второй аргумент - объект, созданный предыдущим шагом (или изначальное значение, переданное через параметр
      ``initial``)

    Функция шага может выглядеть примерно так:

    >>> def create_something(
    >>>     nxt,
    >>>     prev,
    >>>     *args, **kwargs,
    >>> ):
    >>>     # Заворачиваем результат предыдущих шагов в новый объект
    >>>     my = crete_my_object(prev)
    >>>
    >>>     # выполняем следующие шаги, пробросив все дополнительные аргументы
    >>>     # аргументы можно изменять, но крайне желательно пробрасывать все неизвестные аргументы дальше
    >>>     remaining_result = nxt(my, *args, **kwargs)
    >>>
    >>>     # Делаем ещё что-нибудь с результатом работы всех последующих шагов
    >>>     # Делать с ним что-то не обязательно, но вернуть ``nxt(...)`` как правило, нужно
    >>>     return wrap_result(remaining_result)

    Args:
        steps:
            шаги операции
        initial:
            начальное значение
        *args:
            дополнительные позиционные аргументы
        **kwargs:
            дополнительные именованные аргументы

    Returns:
        результат работы операции
    """

    def _call_wrapper(s: Collection[OperationStep], prev, *a, **kw):
        if len(s) == 0:
            return prev

        step, *rest = s

        return step.step(partial(_call_wrapper, rest), prev, *a, **kw)

    return _call_wrapper(tuple(steps), initial, *args, **kwargs)


async def call_all_parallel_async(steps: Iterable[OperationStep], *args, **kwargs) -> Collection[asyncio.Task]:
    """
    Подготавливает Task'и для параллельного асинхронного запуска шагов в текущем Event Loop'е (и его executor'е).

    NOTE: Полученные Task'и нужно заawait'ить. Как правило, для этого можно использовать ``asyncio.gather``:

    >>> await asyncio.gather(*await call_all_parallel_async(...))

    Если шаг является асинхронной функцией, то он запускается в текущем event loop'е, если не асинхронной - то он
    запускается в executor'е, связанном с текущим event loop'ом.

    Независимые шаги запускаются параллельно.

    Args:
        steps:
            последовательность шагов.
        *args, **kwargs:
            аргументы, с которыми будут вызваны шаги
    """
    loop = asyncio.get_running_loop()

    steps_list: list[OperationStep] = list(steps)

    dependencies: dict[str, set[str]] = {step.name: set(step.dependencies) for step in steps_list}

    for step in steps_list:
        if not callable(step.step):
            raise TypeError(
                f"Неподдерживаемый тип шага {step}: {type(step.step)}"
            )

        for r_dep in step.reverse_dependencies:
            if r_dep in dependencies:
                dependencies[r_dep].add(step.name)

    tasks: dict[str, asyncio.Task] = {}

    async def _run_step(step: OperationStep):
        await asyncio.gather(*[tasks[dep] for dep in dependencies[step.name] if dep in tasks])

        try:
            if asyncio.iscoroutinefunction(step.step):
                await step.step(*args, **kwargs)
            else:
                await loop.run_in_executor(
                    None,
                    partial(step.step, *args, **kwargs),
                )
        except asyncio.CancelledError:
            pass

    for s in steps_list:
        tasks[s.name] = loop.create_task(_run_step(s), name=s.name)

    return list(tasks.values())
