"""
Содержит базовые классы и типы, связанные с компонентами голосового ассистента, отвечающими за логику ведения диалога.
"""

from abc import ABCMeta, abstractmethod, ABC
from typing import Optional, Union, Callable, Generator, TypeVar, Any, Type, Collection, Tuple, ContextManager, Protocol

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
    'OutputChannelPool',
    'OutputChannel',
    'OutputChannelNotFoundError',
    'TextOutputChannel',
    'SpeechOutputChannel',
    'AudioOutputChannel',
    'InboundMessage',
    'Brain',
]


class OutputChannel:
    """
    Канал, по которому ассистент может направлять ответные сообщения в том или ином виде.
    """


TChan = TypeVar('TChan', bound=OutputChannel)


class OutputChannelNotFoundError(Exception):
    def __init__(self, cla55: Type[OutputChannel]):
        super().__init__(f'Не удалось подобрать канал типа {cla55}')


class OutputChannelPool(ABC):
    """
    Набор (пул) каналов вывода.
    """

    @abstractmethod
    def get_channels(self, typ: Type[TChan]) -> Collection[TChan]:
        """
        Возвращает каналы из этого пула, наследующие заданный класс.

        Notes:
            Из-за бага в mypy, проверка типов выдаёт ошибку если передавать абстрактный класс первым аргументом.
        Args:
            typ:
                необходимый тип канала
        Returns:
            коллекция каналов, соответствующих запросу
        Raises:
            OutputChannelNotFoundError - если подходящих каналов не найдено
        """


class InboundMessage(ABC):
    """
    Входящее сообщение от пользователя.

    Может представлять собой как текстовое сообщение, набранное в мессенджере или консоли (очевидно) так и распознанную
    голосовую команду (чуть менее очевидно) или некий результат предварительной обработки таковых (возможно, не
    очевидно).
    """

    @abstractmethod
    def get_text(self) -> str:
        """
        Возвращает текст сообщения в каноническом формате.

        С.м. ``convert_to_canonical``.

        Returns:
            текст сообщения в каноническом формате
        """

    @abstractmethod
    def get_related_outputs(self) -> OutputChannelPool:
        """
        Возвращает пул каналов вывода, через которые следует отвечать на это сообщение.

        Returns:
            пул каналов вывода, через которые следует отвечать на это сообщение
        """

    def get_original(self) -> 'InboundMessage':
        """
        Возвращает исходное сообщение если данное сообщение является обёрткой над другим сообщением.

        Для любого сообщения m истинно следующее:
        ``m.get_original().get_original() is m.get_original()``

        Returns:
            исходное сообщение, отправленное пользователем
        """
        return self


class Brain(metaclass=ABCMeta):
    """
    API голосового ассистента, доступный плагинам, реализующим средства ввода/вывода (распознание/синтез речи, обмен
    сообщениями через мессенджеры и т.д.).
    """

    @abstractmethod
    def send_messages(
            self,
            outputs: OutputChannelPool,
    ) -> ContextManager[Callable[[InboundMessage], None]]:
        """
        Позволяет отправлять сообщения голосовому ассистенту.

        >>> brain: Brain = ...
        >>>
        >>> with brain.send_messages(outputs=...,) as send_message:
        >>>     msg = ... # синхронное получение очередного входящего сообщения
        >>>
        >>>     send_message(msg)

        Args:
            outputs:
                пул каналов вывода
        Returns:
            менеджер контекста, предоставляющий функцию отправки сообщения
        """


class VAApi(metaclass=ABCMeta):
    """
    API голосового ассистента, доступный плагинам, добавляющим дополнительные команды/скиллы.
    """

    @abstractmethod
    def get_outputs(self) -> OutputChannelPool:
        """
        Возвращает пул всех доступных каналов вывода.

        Returns:
            пул всех доступных каналов вывода
        """

    def say(self, text: str, **kwargs):
        """
        Воспроизводит переданную фразу через основной канал вывода.

        Блокирует выполнение до завершения воспроизведения.

        Может быть вызван только из обработчиков контекста (``VAContext.handle_*``) и во взаимодействиях
        (``VAActiveInteraction.act``).
        При вызове из других мест - поведение не определено.

        Args:
            text: текст фразы
            **kwargs: дополнительные опции
        """
        ch: TextOutputChannel

        # Type check doesn't work properly, https://github.com/python/mypy/issues/5374 may be related
        ch, *_ch = self.get_outputs().get_channels(TextOutputChannel)  # type: ignore

        ch.send(text, **kwargs)

    def play_audio(self, file_path: str, **kwargs):
        """
        Воспроизводит аудио-файл.

        Блокирует выполнение до завершения воспроизведения.

        Может быть вызван только из обработчиков контекста (VAContext.handle_*) и во взаимодействиях
        (VAActiveInteraction.act).
        При вызове из других мест - поведение не определено.

        Args:
            file_path: путь к файлу
            **kwargs: дополнительные опции
        """
        ch: AudioOutputChannel

        # Type check doesn't work properly, https://github.com/python/mypy/issues/5374 may be related
        ch, *_ch = self.get_outputs().get_channels(AudioOutputChannel)  # type: ignore

        ch.send_file(file_path, **kwargs)

    @abstractmethod
    def submit_active_interaction(
            self,
            interaction: 'VAActiveInteractionSource',
            *,
            related_message: Optional['InboundMessage'] = None,
    ):
        """
        Начинает активное взаимодействие.

        Args:
            interaction:
            related_message:
                ранее полученное сообщение, связанное с взаимодействием.
                Это сообщение будет доступно через метод ``get_message`` взаимодействиям, использующим ``VAApiExt``.
                Если сообщение не передано явно, то реализация ``VAApi`` может попытаться обнаружить последнее
                полученное сообщение и использовать его.
        """


class VAApiExt(VAApi, ABC):
    """
    Расширенный API голосового ассистента, доступный плагинам, добавляющим сценарии диалогов без реализации собственных
    подклассов VAContext.

    Содержит методы управляющие поведением контекста, в который оборачивается функция, предоставленная плагином.

    Todo:
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

    @abstractmethod
    def get_message(self) -> InboundMessage:
        """
        Возвращает полный объект сообщения.

        Raises:
            RuntimeError - если сведений о предыдущем сообщении нет.
            Например, при вызове из функции активного взаимодействия, до получения первого ответного сообщения и при
            отправке взаимодействия (``submit_active_interaction``) связанное сообщение не было предоставлено
            (через параметр ``related_message`` или неявно).
        """

    def get_outputs_preferring_relevant(self, typ: Type[TChan]) -> Collection[TChan]:
        """
        Подбирает каналы вывода, соответствующие заданным критериям, предпочитает каналы релевантные последнему
        полученному сообщению.

        Args:
            typ:
                необходимый тип канала
        Returns:
            коллекция каналов, соответствующих запросу
        Raises:
            OutputChannelNotFoundError - если подходящих каналов не найдено
        """
        try:
            return self.get_message().get_related_outputs().get_channels(typ)
        except OutputChannelNotFoundError:
            ...
        except RuntimeError:
            ...

        return self.get_outputs().get_channels(typ)

    def say(self, text: str, **kwargs):
        """
        Отправляет текстовое сообщение.

        Args:
            text:
                текст сообщения
            **kwargs:
                дополнительные опции

        Raises:
            OutputChannelNotFoundError - если не найден канал вывода, поддерживающий текстовые сообщения (вероятность
            этого крайне мала)
        """
        ch: TextOutputChannel

        # Type check doesn't work properly, https://github.com/python/mypy/issues/5374 may be related
        ch, *_ch = self.get_outputs_preferring_relevant(TextOutputChannel)  # type: ignore

        ch.send(text, **kwargs)

    def say_speech(self, text: str, **kwargs):
        """
        Аналогично ``say(...)`` выводит заданный текст, но выбирает только каналы, преобразующие текст в речь.

        Args:
            text:
                текст сообщения
            **kwargs:
                дополнительные опции

        Raises:
            OutputChannelNotFoundError - если не найден подходящий канал вывода
        """
        ch: SpeechOutputChannel

        # Type check doesn't work properly, https://github.com/python/mypy/issues/5374 may be related
        ch, *_ch = self.get_outputs_preferring_relevant(SpeechOutputChannel)  # type: ignore

        ch.send(text, **kwargs)

    def play_audio(self, file_path: str, **kwargs):
        """
        Воспроизводит аудио-файл.

        Args:
            file_path:
                путь к файлу
            **kwargs:
                дополнительные опции

        Raises:
            OutputChannelNotFoundError - если не найден канал вывода, поддерживающий воспроизведение аудио-файлов
        """
        ch: AudioOutputChannel

        # Type check doesn't work properly, https://github.com/python/mypy/issues/5374 may be related
        ch, *_ch = self.get_outputs_preferring_relevant(AudioOutputChannel)  # type: ignore

        ch.send_file(file_path, **kwargs)


class TextOutputChannel(ABC, OutputChannel):
    """
    Канал, принимающий текстовые сообщения.

    Например, TTS, консоль или мессенджер.
    """

    @abstractmethod
    def send(self, text: str, **kwargs):
        """
        Отправляет текстовое сообщение.

        Блокирует выполнение до окончания отправки сообщения.
        Семантика "окончания отправки сообщения" может отличаться в зависимости от типа канала.
        Для TTS окончанием может считаться окончание воспроизведения озвученного текста, для мессенджера - успешная
        доставка сообщения до сервера мессенджера или прочтение сообщения пользователем.

        Args:
            text:
                текст сообщения
            **kwargs:
                дополнительные опции, набор зависит от конкретной реализации класса.
                Реализации должны игнорировать неизвестные им опции.
        """


class SpeechOutputChannel(TextOutputChannel, ABC):
    """
    Текстовый канал, выведенный в который текст будет преобразован в речь.
    """


class AudioOutputChannel(ABC, OutputChannel):
    """
    Канал, способный воспроизводить звуковые сигналы/сообщения.
    """

    @abstractmethod
    def send_file(self, file_path: str, **kwargs):
        """
        Воспроизводит аудио-файл в этот канал.

        Блокирует выполнение до окончания воспроизведения.

        Args:
            file_path:
                путь к аудио-файлу
            **kwargs:
                дополнительные опции, набор зависит от конкретной реализации класса.
                Реализации должны игнорировать неизвестные им опции.
        """


class VAContext(metaclass=ABCMeta):
    """
    Контекст диалога, определяет поведение ассистента в некотором состоянии.
    """

    @abstractmethod
    def handle_command(self, va: VAApi, message: InboundMessage) -> Optional['VAContext']:
        """
        Вызывается при получении новой голосовой команды.

        Args:
            va:
            message: входящее сообщение

        Returns: контекст для продолжения диалога или None для завершения диалога
        """

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

# yield type, send type, return type
VAContextGenerator = Generator[Optional[Union[str, Tuple[str, float]]], str, Optional[str]]

VAContextSource = Union[
    VAContext,
    Type[VAContext],
    Callable[[VAApiExt, str], None],
    Callable[[VAApiExt, str], VAContextGenerator],
    tuple[Callable[[VAApiExt, str, T], None], T],
    tuple[Callable[[VAApiExt, str, T], VAContextGenerator], T],
    VAContextSourcesDict,
]


class VAContextConstructor(Protocol):
    """
    Функция, создающая контекст (``VAContext``) из исходного объекта (``VAContextSource``).
    """

    def __call__(self, src: VAContextSource, **kwargs: Any) -> VAContext:
        ...


class VAActiveInteraction(metaclass=ABCMeta):
    """
    Взаимодействие, осуществляемое "по инициативе" ассистента.

    Например, сообщение о том, что сработал таймер.

    Может начать новый диалог, по завершение которого, ассистент вернётся к текущему диалогу. Например:

    > бла бла бла

    < бла бла бла бла

        < Тебе пришло новое письмо # VAActiveInteraction прерывает изначальный диалог

        > Прочитай

        < бла бла бла (текст письма)

        > это спам

        < письмо отмечено как спам

    > бла бла бал # продолжение изначального диалога
    """

    @abstractmethod
    def act(self, va: VAApi) -> Optional[VAContext]:
        """
        Осуществляет взаимодействие.

        Args:
            va:

        Returns: контекст нового диалога или None если начинать новый диалог не нужно
        """


VAActiveInteractionSource = Union[
    VAActiveInteraction,
    Type[VAActiveInteraction],
    Callable[[VAApiExt], Optional[VAContextGenerator]],
]
