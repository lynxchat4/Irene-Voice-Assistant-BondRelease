import sys
from collections import Iterable
from glob import iglob
from os.path import abspath, join, normpath, dirname
from pathlib import Path


def match_files(patterns: Iterable[str]) -> Iterable[str]:
    """
    Ищет файлы, соответствующие заданным шаблонам.

    Шаблоны работают аналогично стандартному ``glob``, однако добавлена возможность использования переменных:

    - ``{user_home}`` - путь к домашней папке пользователя
    - ``{python_path}`` - путь к папке с пакетами python.
      Функция будет перебирать все папки, используемые интерпретатором.
    - ``{irene_path}`` - путь к папке корневого пакета Ирины

    Args:
        patterns:
            шаблоны для поиска файлов
    Returns:
        пути к найденным файлам
    """
    matching = set()

    params = dict(
        user_home=str(Path.home()),
        irene_path=normpath(join(dirname(__file__), '..')),
    )

    def match_glob(g: str):
        for match in iglob(g, recursive=True):
            matching.add(abspath(match))

    for pattern in patterns:
        if '{python_path}' in pattern:
            for pypath in sys.path:
                params['python_path'] = pypath
                match_glob(pattern.format(**params))
        else:
            match_glob(pattern.format(**params))

    return matching
