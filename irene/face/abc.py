"""
Содержит базовые классы для компонентов, отвечающих за ввод и вывод сообщений.
"""

from abc import ABC, abstractmethod

from irene.utils.metadata import Metadata

__all__ = [
    'TTS',
    'ImmediatePlaybackTTS',
    'TTSResultFile',
    'FileWritingTTS',
    'LocalInput',
    'Muteable',
    'MuteGroup',
]

from contextlib import contextmanager

from typing import Optional, Callable, ContextManager, Iterable


class TTS(Metadata, ABC):
    """
    Базовый класс для фасада TTS (Text-To-Speech) движка.
    """

    def get_name(self) -> str:
        """
        Возвращает имя TTS-движка.
        """
        return self.__class__.__name__

    def get_settings_hash(self) -> str:
        """
        Возвращает хеш от текущих настроек TTS-движка.

        При одинаковых настройках, возвращаемое значение должно оставаться одинаковым при перезапуске программы.
        Как следствие, при вычислении результата нельзя использовать стандартную функцию ``hash``, которая использует
        случайный seed.
        """
        return 'unknown'


class ImmediatePlaybackTTS(TTS):
    """
    TTS, который может воспроизводить синтезированную речь самостоятельно.
    """

    @abstractmethod
    def say(self, text: str, **kwargs):
        """
        Произносит заданный текст.

        Блокирует выполнение до завершения произношения текста.

        Args:
            text:
                текст
            **kwargs:
                дополнительные опции.
                Реализации должны игнорировать неизвестные им опции.
        """


class TTSResultFile(ABC):
    """
    Содержит сведения об аудио-файле, содержащем результат работы TTS-движка (произнесённый текст).
    """

    @abstractmethod
    def get_full_path(self) -> str:
        """
        Возвращает полный абсолютный путь к файлу.
        """

    @abstractmethod
    def release(self):
        """
        Сообщает, что файл больше не нужен.

        Вызов может привести к удалению файла.
        """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


class FileWritingTTS(TTS):
    """
    TTS, который может записать синтезированную речь в файл.
    """

    @abstractmethod
    def say_to_file(self, text: str, file_base_path: Optional[str] = None, **kwargs) -> TTSResultFile:
        """
        Синтезирует речь и записать её в файл.

        Args:
            text:
                текст
            file_base_path:
                частичный (без расширения) путь к файлу, в который нужно сохранить результат или ``None`` если
                вызывающей стороне неважно расположение и имя файла.
            **kwargs:
                дополнительные опции.
                Реализации должны игнорировать неизвестные им опции.

        Returns:
            Объект ``TTSResultFile`` содержащий сведения о файле, содержащем результат преобразования текста в речь.
        """


class LocalInput(ABC):
    """
    Локальный метод ввода текста.
    Как правило, представляет собой сочетание метода записи звука и метода распознания речи.
    """

    @abstractmethod
    def run(self) -> ContextManager[tuple[Iterable[str], Callable[[], None]]]:
        """
        Запускает ввод текста и предоставляет итератор, по введённым командам.

        >>> li: LocalInput = ...
        >>> with li.run() as (lines, stop):
        >>>     # stop() можно вызвать из другого потока чтобы прервать цикл ввода
        >>>     for line in lines:
        >>>         # Генератор lines будет блокировать поток до получения очередной строки введённого текста
        >>>         # и завершится после вызова функции stop.
        >>>         ... # Делаем что-нибудь с введённой строкой
        """


class Muteable(ABC):
    """
    Аудио-вход (локальный или удалённый), который можно временно (как правило, на время воспроизведения ответа
    ассистента) заглушить.
    """

    @abstractmethod
    def mute(self):
        """
        Временно заглушает аудио-вход.
        """

    @abstractmethod
    def unmute(self):
        """
        Заново включает аудио-вход.
        """


class MuteGroup(Muteable):
    """
    Группа аудио-входов, которые можно заглушать одновременно.
    """

    @abstractmethod
    def add_item(self, item: Muteable) -> Callable[[], None]:
        """
        Добавляет один вход в группу.

        Предполагается, что вход не заглушён.
        Если входы группы заглушены, то добавленный вход будет немедленно заглушён.

        Returns:
            Функция, удаляющая добавленный вход из группы
        """

    @abstractmethod
    def mute(self):
        """
        Заглушает все входы в группе.

        Входы будут заглушены, пока метод ``unmute()`` не будет вызван столько же раз, сколько был вызван метод
        ``mute()``.
        """

    @abstractmethod
    def unmute(self):
        """
        Заново включает все входы.

        Чтобы вызов этого метода действительно включил входы, на каждый вызов ``mute()`` должен приходиться
        соответствующий вызов ``unmute()``.

        Raises:
            AssertionError:
                если метод ``unmute()`` был вызван больше раз, чем метод ``mute()``
        """

    @contextmanager
    def muted(self):
        """
        Менеджер контекста, заглушающий все входы в группе на время выполнения кода внутри блока ``with``.

        >>>    microphones: MuteGroup = ...
        >>>
        >>>    ...
        >>>
        >>>    with microphones.muted():
        >>>        # Воспроизводим голосовой ответ, который, без заглушения микрофонов, мог бы быть распознан как ответ
        >>>        # пользователя
        >>>        play_response_audio()
        """
        try:
            self.mute()
            yield
        finally:
            self.unmute()
