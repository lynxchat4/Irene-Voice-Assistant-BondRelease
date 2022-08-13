from abc import ABCMeta, abstractmethod
from typing import Optional, Union, Callable, Generator, TypeVar, Any

__all__ = ['VAApi', 'VAContext', 'VAContextSource', 'VAContextSourcesDict', 'VAContextConstructor']


class VAApi(metaclass=ABCMeta):
    @abstractmethod
    def say(self, text: str):
        ...


class VAContext(metaclass=ABCMeta):
    @abstractmethod
    def handle_command(self, core: VAApi, text: str) -> Optional['VAContext']:
        """
        Вызывается при получении новой голосовой команды.

        Args:
            core:
            text: текст команды

        Returns: контекст для продолжения диалога или None для завершения диалога
        """
        ...

    def handle_timeout(self, core: VAApi) -> Optional['VAContext']:
        """
        Вызывается при истечении таймаута ожидания следующей команды.

        Реализация по-умолчанию завершает диалог.

        Returns: контекст для продолжения диалога или None для завершения диалога

        Args:
            core:
        """
        return None


T = TypeVar('T')

# VAContextSourcesDict = dict[str, 'VAContextSource']
VAContextSourcesDict = dict[str, Any]

VAContextSource = Union[
    VAContext,
    Callable[[VAApi, str], None],
    Callable[[VAApi, str], Generator[str, str, str]],
    tuple[Callable[[VAApi, str, T], None], T],
    tuple[Callable[[VAApi, str, T], Generator[str, str, str]], T],
    VAContextSourcesDict,
]

VAContextConstructor = Callable[[VAContextSource], VAContext]
