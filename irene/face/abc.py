"""
Содержит базовые классы для компонентов, отвечающих за ввод и вывод сообщений.
"""

from abc import ABC, abstractmethod

__all__ = [
    'TTS',
    'ImmediatePlaybackTTS',
    'TTSResultFile',
    'FileWritingTTS',
]

from typing import Optional


class TTS(ABC):
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
        """
        return 'unknown'

    def terminate(self):
        """
        Завершает работу движка и освобождает все занятые им ресурсы.
        """
        pass


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
        Синтезировать речь и записать её в файл.

        Args:
            text:
                текст
            file_base_path:
                частичный (без расширения) путь к файлу, в который нужно сохранить результат или ``None`` если
                вызывающей стороне не важно расположение и имя файла.
            **kwargs:
                дополнительные опции.
                Реализации должны игнорировать неизвестные им опции.

        Returns:
            Объект ``TTSResultFile`` содержащий сведения о файле, содержащем результат преобразования текста в речь.
        """
