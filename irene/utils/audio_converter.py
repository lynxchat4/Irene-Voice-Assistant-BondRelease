from abc import ABC, abstractmethod


class ConversionError(Exception):
    pass


class AudioConverter(ABC):
    @abstractmethod
    def convert(
            self,
            file: str,
            to_format: str,
    ) -> str:
        """
        Преобразует заданный аудио-файл в нужный формат.

        Args:
            file:
                путь к исходному файлу
            to_format:
                название целевого формата в форме, поддерживаемой ffmpeg - "ogg", "mp3", "wav", и т.д.

        Returns:
            путь к созданному преобразованному файлу

        Raises:
            ConversionError
        """

    @staticmethod
    def get_converted_file_path(file: str, to_format: str):
        return f'{file}.converted.{to_format}'
