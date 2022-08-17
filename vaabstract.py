from abc import ABCMeta, abstractmethod, ABC
from typing import Optional, Union, Callable, Generator, TypeVar, Any

__all__ = [
    'VAApi',
    'VAApiExt',
    'VAContext',
    'VAContextSource',
    'VAContextGenerator',
    'VAContextSourcesDict',
    'VAContextConstructor',
    'VAActiveInteraction',
    'VAActiveInteractionSource',
    'TTS',
    'AudioFilePlayer',
]


class VAApi(metaclass=ABCMeta):
    """
    API голосового ассистента, доступный плагинам.
    """

    @abstractmethod
    def say(self, text: str):
        """
        Воспроизводит переданную фразу через основной канал вывода.

        Блокирует выполнение до завершения воспроизведения.

        Может быть вызван только из обработчиков контекста (``VAContext.handle_*``) и во взаимодействиях
        (``VAActiveInteraction.act``).
        При вызове из других мест - поведение не определено.

        Args:
            text: текст фразы
        """
        ...

    def play_voice_assistant_speech(self, text: str):
        return self.say(text)

    @abstractmethod
    def play_audio(self, file_path: str):
        """
        Воспроизводит аудио-файл.

        Блокирует выполнение до завершения воспроизведения.

        Может быть вызван только из обработчиков контекста (VAContext.handle_*) и во взаимодействиях
        (VAActiveInteraction.act).
        При вызове из других мест - поведение не определено.

        Args:
            file_path: путь к файлу
        """
        ...

    @abstractmethod
    def submit_active_interaction(self, interaction: 'VAActiveInteractionSource'):
        """
        Начинает активное взаимодействие.

        Args:
            interaction:
        """
        ...


class VAApiExt(VAApi, ABC):
    """
    Расширенный API голосового ассистента, доступный плагинам, добавляющим сценарии диалогов без реализации собственных
    подклассов VAContext.

    Содержит методы управляющие поведением контекста, в который оборачивается функция, предоставленная плагином.

    Todos:
        - Добавить действия на случай прерывания/восстановления диалога
        - Добавить настройку времени ожидания следующей команды без переключения контекста
    """

    @abstractmethod
    def context_set(self, ctx: 'VAContextSource', timeout: Optional[float] = None):
        """
        Передаёт управление переданному контексту после завершения текущего обработчика.

        Может быть вызван только из обработчиков контекста (VAContext.handle_*) и во взаимодействиях
        (VAActiveInteraction.act).
        При вызове из других мест - поведение не определено.

        Args:
            ctx: контекст, которому будет передано управление после завершения текущего обработчика
            timeout: время ожидания команды для следующего контекста
        """
        ...


class TTS(metaclass=ABCMeta):
    """
    Фасад для сервиса преобразования текста в речь (TTS, Text To Speech).
    """

    @abstractmethod
    def say(self, text: str):
        """
        Озвучивает заданный текст.

        Блокирует выполнение до завершения воспроизведения.

        Args:
            text: текст, который нужно воспроизвести
        """
        ...


class AudioFilePlayer(metaclass=ABCMeta):
    """
    Фасад для сервиса, воспроизводящего аудио-файлы.

    Используется для воспроизведения неречевых звуков (например, сигналов таймера) а так же может использоваться
    некоторыми реализациями TTS для воспроизведения синтезированной речи.
    """

    @abstractmethod
    def play(self, file_path: str):
        """
        Воспроизводит звук из заданного файла.

        Блокирует выполнение до окончания воспроизведения.

        Args:
            file_path: путь к аудио-файлу
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

    def handle_interrupt(self, va: VAApi) -> Optional['VAContext']:
        """
        Вызывается при прерывании диалога.

        Args:
            va:

        Returns: контекст, который будет использоваться при продолжении диалога или None если диалог должен быть
                 завершён
        """
        return self

    def handle_restore(self, va: VAApi) -> Optional['VAContext']:
        """
        Вызывается при продолжении диалога после прерывания.

        Args:
            va:

        Returns: контекст, который должен использоваться далее или None если диалог завершён
        """
        return self


T = TypeVar('T')

# VAContextSourcesDict = dict[str, 'VAContextSource'] # пока не поддерживается в mypy
VAContextSourcesDict = dict[str, Any]

VAContextGenerator = Generator[Optional[str], str, Optional[str]]

VAContextSource = Union[
    VAContext,
    Callable[[VAApiExt, str], None],
    Callable[[VAApiExt, str], VAContextGenerator],
    tuple[Callable[[VAApiExt, str, T], None], T],
    tuple[Callable[[VAApiExt, str, T], VAContextGenerator], T],
    VAContextSourcesDict,
]

VAContextConstructor = Callable[[VAContextSource], VAContext]


class VAActiveInteraction(metaclass=ABCMeta):
    """
    Взаимодействие, осуществляемое "по инициативе" ассистента.

    Например, сообщение о том, что сработал таймер.

    Может начать новый диалог, по завершение которого, ассистент вернётся к текущему диалогу. Например:

    > блаблабла

    < блаблаблабла

        < Тебе пришло новое письмо # VAActiveInteraction прерывает изначальный диалог

        > Прочитай

        < блаблабла (текст письма)

        > это спам

        < письмо отмечено как спам

    > блаблабал # продолжение изначального диалога
    """

    @abstractmethod
    def act(self, va: VAApi) -> Optional[VAContext]:
        """
        Осуществляет взаимодействие.

        Args:
            va:

        Returns: контекст нового диалога или None если начинать новый диалог не нужно
        """
        ...


VAActiveInteractionSource = Union[
    VAActiveInteraction,
    Callable[[VAApiExt], Optional[VAContextGenerator]],
]
