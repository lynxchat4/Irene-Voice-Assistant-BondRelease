from typing import Any


def snapshot_hash(obj: Any) -> int:
    """
    Аналог встроенной функции hash(), но позволяющий считать хеш от текущего состояния некоторых изменяемых объектов:
    - словарей
    - списков
    """
    if isinstance(obj, dict):
        h = hash(dict)

        for k, v in obj.items():
            h = h ^ hash((k, snapshot_hash(v)))

        return h

    elif isinstance(obj, list):
        obj = tuple(snapshot_hash(it) for it in obj)

    return hash(obj)
