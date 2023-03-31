import sys
from collections import Iterable
from glob import iglob
from os.path import abspath
from pathlib import Path
from random import choice
from typing import Optional, Union

PathVariableValue = Union[str, Iterable[str]]

_global_variables: dict[str, PathVariableValue] = dict(
    user_home=str(Path.home()),
    python_path=[str(it) for it in sys.path],
)


def register_variable(name: str, value: PathVariableValue):
    """
    Добавляет переменную, которую затем можно будет использовать в шаблонах путей файлов.

    Args:
        name:
            имя переменной
        value:
            значение переменной
    """
    _global_variables[name] = value


def match_files(
        patterns: Iterable[str],
        *,
        override_vars: Optional[dict[str, PathVariableValue]] = None,
) -> Iterable[str]:
    """
    Ищет существующие файлы, соответствующие заданным шаблонам.

    Шаблоны работают аналогично стандартному ``glob``, однако добавлена возможность использования переменных:

    - ``{user_home}`` - путь к домашней папке пользователя
    - ``{irene_path}`` - путь к папке корневого пакета Ирины
    - ``{python_path}`` - путь к папке с пакетами python.
      Функция будет перебирать все папки, используемые интерпретатором.

    Args:
        patterns:
            шаблоны для поиска файлов
        override_vars:
            дополнительные переменные, для использования в шаблонах
    Returns:
        пути к найденным файлам

    Raises:
        ValueError если один из шаблонов использует переменную, значение которой не определено
    """
    if isinstance(patterns, str):
        patterns = patterns,

    matching = set()

    for pattern in patterns:
        for substituted in substitute_pattern(pattern, override_vars=override_vars):
            for match in iglob(substituted, recursive=True):
                matching.add(abspath(match))

    return matching


def pick_random_file(
        patterns: Iterable[str],
        *,
        override_vars: Optional[dict[str, PathVariableValue]] = None,
) -> str:
    """
    Выбирает случайный файл среди файлов, соответствующих хотя бы одному из заданных шаблонов.

    Args:
        patterns:
            шаблоны для поиска файлов
        override_vars:
            дополнительные переменные, для использования в шаблонах

    Returns:
        Путь к одному случайно выбранному файлу из файлов, соответствующих любому из переданных шаблонов

    Raises:
        FileNotFoundError если нет ни одного файла, соответствующего хотя бы одному из переданных шаблонов
        ValueError если один из шаблонов использует переменную, значение которой не определено
    """
    files = list(match_files(patterns, override_vars=override_vars))

    if len(files) == 0:
        raise FileNotFoundError()

    return choice(files)


def substitute_pattern(
        pattern: str,
        *,
        override_vars: Optional[dict[str, PathVariableValue]] = None,
) -> Iterable[str]:
    """
    Подставляет переменные в заданный шаблон.

    Args:
        pattern:
            Шаблон пути файла
        override_vars:
            Дополнительные переменные

    Returns:
        Iterable всех вариантов подстановки переменных

    Raises:
        ValueError если шаблон использует переменную, значение которой не определено
    """
    all_vars: dict[str, PathVariableValue] = {
        **_global_variables, **(override_vars or {})}

    for k, v in all_vars.items():
        if isinstance(v, str):
            continue

        if k not in pattern:
            continue

        if ('{' + k + '}') not in pattern:
            continue

        for value in v:
            all_vars[k] = value
            yield from substitute_pattern(pattern, override_vars=all_vars)

        return

    try:
        yield pattern.format(**all_vars)
    except KeyError as e:
        raise ValueError(
            f"Неизвестная переменная '{e.args[0]}' в шаблоне пути файла '{pattern}'") from None


def substitute_patterns(
        patterns: Iterable[str],
        *,
        override_vars: Optional[dict[str, PathVariableValue]] = None,
) -> Iterable[str]:
    """
    Подставляет переменные в заданный шаблон или несколько шаблонов.

    Args:
        patterns:
            Шаблон пути файла или коллекция таких шаблонов
        override_vars:
            Дополнительные переменные

    Returns:
        Iterable всех вариантов подстановки переменных

    Raises:
        ValueError если один из шаблон ов использует переменную, значение которой не определено
    """
    if isinstance(patterns, str):
        return substitute_pattern(patterns, override_vars=override_vars)

    for pattern in patterns:
        yield from substitute_pattern(pattern, override_vars=override_vars)


def first_substitution(
        pattern: str,
        *,
        override_vars: Optional[dict[str, PathVariableValue]] = None,
):
    """
    Возвращает один из вариантов подстановки переменных в заданный шаблон.

    Args:
        pattern:
            Шаблон пути файла
        override_vars:
            Дополнительные переменные

    Returns:
        Результат подстановки переменных в шаблон.

    Raises:
        ValueError если шаблон использует переменную, значение которой не определено
    """
    return next(iter(substitute_pattern(pattern, override_vars=override_vars)))
