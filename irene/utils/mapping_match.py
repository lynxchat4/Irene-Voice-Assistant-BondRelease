from typing import Any, Mapping


def mapping_match(a: Mapping[Any, Any], b: Mapping[Any, Any]) -> bool:
    """
    Возвращает ``True`` если и только если для каждой пары ключ-значение в словаре ``b`` есть точно такая же пара в
    словаре ``a``.
    """
    try:
        for k, v in b.items():
            if a[k] != v:
                return False
    except KeyError:
        return False

    return True
