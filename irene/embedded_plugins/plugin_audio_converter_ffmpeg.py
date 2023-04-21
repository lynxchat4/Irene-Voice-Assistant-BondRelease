import subprocess
from logging import getLogger
from typing import Optional, TypedDict

from irene.plugin_loader.magic_plugin import step_name
from irene.utils.audio_converter import ConversionError, AudioConverter
from irene.utils.executable_files import is_executable, get_executable_path

name = 'audio_converter_ffmpeg'
version = '0.2.0'


class _Config(TypedDict):
    forceFFMpegPath: Optional[str]


config: _Config = {
    'forceFFMpegPath': None,
}

config_comment = """
Настройки конвертирования аудио-файлов при помощи ffmpeg.

Параметры:
- `forceFFMpegPath`   - Путь к исполняемому файлу ffmpeg.
                        Если путь не установлен или некорректен, то плагин попытается искать ffmpeg в `$PATH`.
"""

_logger = getLogger(name)


def _get_ffmpeg_path() -> Optional[str]:
    if (forced_path := config['forceFFMpegPath']) is not None:
        if is_executable(forced_path):
            return forced_path

        _logger.warning(
            "Исполняемый файл ffmpeg по пути %s не существует. Пытаюсь искать в других местах.",
            forced_path,
        )

    return get_executable_path('ffmpeg')


class _AudioConverterImpl(AudioConverter):
    __slots__ = ('_ffmpeg_path',)

    def __init__(self, ffmpeg_path: str):
        self._ffmpeg_path = ffmpeg_path

    def convert_to(self, file: str, dst_file: str, to_format: str):
        try:
            command = [
                self._ffmpeg_path,
                '-hide_banner',
                '-y',
                '-i', file,
                dst_file,
            ]

            _logger.debug("%s", command)

            subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as e:
            _logger.error(
                "Вывод %s при преобразовании %s в %s:\n%s",
                self._ffmpeg_path,
                file,
                dst_file,
                e.output,
            )
            raise ConversionError(
                f"Вызов ffmpeg для конвертирования {file} в {dst_file} завершился с ошибкой (код {e.returncode})"
            )


def _create_ffmpeg_converter() -> Optional[AudioConverter]:
    ffmpeg_path = _get_ffmpeg_path()

    if ffmpeg_path is not None:
        _logger.debug(
            "Исполняемый файл ffmpeg найден по пути: %s", ffmpeg_path)
        return _AudioConverterImpl(ffmpeg_path)

    _logger.info("Исполняемый файл ffmpeg не найден")

    return None


@step_name('ffmpeg')
def get_audio_converter(nxt, prev, *args, **kwargs):
    prev = prev or _create_ffmpeg_converter()
    return nxt(prev, *args, **kwargs)
