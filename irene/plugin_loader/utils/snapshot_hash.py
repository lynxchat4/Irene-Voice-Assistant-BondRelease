from hashlib import sha256
from typing import Any, Callable


def make_stable_hash_fn(algorithm=sha256) -> Callable[[Any], int]:
    """
    Создаёт аналог стандартной функции ``hash``, использующую заданный алгоритм из библиотеки hashlib.

    В отличие от стандартной ``hash``, результат выполнения такой функции на одинаковых входных данных будет одинаковым
    при каждом запуске программы.
    """

    def _hash(obj: Any) -> int:
        h = algorithm(str(obj).encode('utf-8'))
        h.update(str(type(obj)).encode('utf-8'))
        return int.from_bytes(h.digest(), 'little')

    return _hash


def snapshot_hash(obj: Any, base_hash: Callable[[Any], int] = make_stable_hash_fn()) -> int:
    """
    Аналог встроенной функции hash(), но позволяющий считать хеш от текущего состояния некоторых изменяемых объектов:
    - словарей
    - списков

    Args:
        obj: объект, хеш которого нужно вычислить
        base_hash: базовая хеш-функция, используется для вычисления хеша неизменяемых объектов.
                    По-умолчанию используется хеш-функция, на основе алгоритма sha256, это обеспечивает повторяемость
                    хешей между запусками программы.
                    Если повторяемость не нужна, то можно передать стандартную функцию ``hash`` в качестве значения
                    этого параметра (её результат для одинаковых значений аргументов может отличаться между запусками
                    программы).
    """
    if isinstance(obj, dict):
        h = base_hash(dict)

        for k, v in obj.items():
            h = h ^ base_hash((k, snapshot_hash(v, base_hash)))

        return h

    elif isinstance(obj, list):
        obj = tuple(snapshot_hash(it, base_hash) for it in obj)

    return base_hash(obj)
