from abc import ABC, abstractmethod
from logging import getLogger
from os import stat, utime
from os.path import isfile
from typing import Optional

_logger = getLogger('audio_converter')


class ConversionError(Exception):
    pass


class AudioConverter(ABC):
    @abstractmethod
    def convert_to(
            self,
            file: str,
            dst_file: str,
            to_format: str,
    ):
        """
        Преобразует заданный аудио-файл в нужный формат.

        Args:
            file:
                путь к исходному файлу
            dst_file:
                путь к конвертированному файлу
            to_format:
                название целевого формата - "ogg", "mp3", "wav", и т.д.

        Raises:
            ConversionError
        """

    def convert(self, file: str, to_format: str, dst_file: Optional[str] = None) -> str:
        """
        Преобразует файл в нужный формат если преобразованный файл ещё не существует.

        Преобразованный файл создаётся автоматически в той же папке, где лежит исходный файл.

        Args:
            file:
                путь к исходному файлу
            to_format:
                название целевого формата - "ogg", "mp3", "wav", и т.д.
            dst_file:
                путь к преобразованному файлу.
                Если ``None``, то будет использован путь, выбранный методом ``get_converted_file_path``.

        Returns:
            путь к преобразованному файлу

        Raises:
            ConversionError
        """
        if not isfile(file):
            raise ValueError(f"{file} не является файлом")

        src_stats = stat(file)
        dst_path = self.get_converted_file_path(file, to_format) if dst_file is None else dst_file

        if isfile(dst_path) and stat(dst_path).st_mtime >= src_stats.st_mtime:
            _logger.debug(
                "Конвертированный файл %s всё ещё актуален, не буду его перезаписывать.",
                dst_path,
            )
            return dst_path

        self.convert_to(file, dst_path, to_format)

        try:
            utime(dst_path, ns=(src_stats.st_mtime_ns, src_stats.st_atime_ns))
        except FileNotFoundError:
            raise ConversionError(f"Конвертер не создал ожидаемый файл {dst_path}")

        return dst_path

    @staticmethod
    def get_converted_file_path(file: str, to_format: str):
        return f'{file}.converted.{to_format}'
