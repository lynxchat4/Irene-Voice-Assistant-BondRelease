from abc import ABCMeta, abstractmethod
from typing import Optional, Union, Callable, Generator, TypeVar, Any

__all__ = ['VAApi', 'VAContext', 'VAContextSource', 'VAContextSourcesDict', 'VAContextConstructor']


class VAApi(metaclass=ABCMeta):
    """
    API голосового ассистента, доступный плагинам.
    """

    @abstractmethod
    def say(self, text: str):
        """
        Воспроизводит переданную фразу через основной канал вывода.

        Блокирует выполнение до завершения воспроизведения.
        TODO: (но это не точно)

        Args:
            text: текст фразы
        """
        ...


class VAContext(metaclass=ABCMeta):
    """
    Контекст диалога, определяет поведение ассистента в некотором состоянии.
    """

    @abstractmethod
    def handle_command(self, va: VAApi, text: str) -> Optional['VAContext']:
        """
        Вызывается при получении новой голосовой команды.

        Args:
            va:
            text: текст команды

        Returns: контекст для продолжения диалога или None для завершения диалога
        """
        ...

    def handle_timeout(self, va: VAApi) -> Optional['VAContext']:
        """
        Вызывается при истечении таймаута ожидания следующей команды.

        Реализация по-умолчанию завершает диалог.

        Returns: контекст для продолжения диалога или None для завершения диалога

        Args:
            va:
        """
        return None

    def get_timeout(self, default: float) -> float:
        """
        Возвращает время (в секундах), в течение которого контекст готов ожидать следующей команды.
        По истечение этого времени, будет вызван метод `handle_timeout`, который может произвести какие-либо действия
        (например, переспросить) и/или переключиться на другой контекст.

        Реализация по-умолчанию возвращает значение по-умолчанию, предоставленное вызывающим компонентом.

        Args:
            default: время ожидания по-умолчанию (в секундах)

        Returns:
            время ожидания следующей команды (в секундах)
        """
        return default


T = TypeVar('T')

# VAContextSourcesDict = dict[str, 'VAContextSource'] # пока не поддерживается в mypy
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
