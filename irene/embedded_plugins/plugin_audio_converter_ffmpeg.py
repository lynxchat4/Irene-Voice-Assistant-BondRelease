import subprocess
from logging import getLogger
from os import stat
from os.path import isfile
from typing import Optional

from irene.plugin_loader.magic_plugin import step_name
from irene.utils.audio_converter import ConversionError, AudioConverter
from irene.utils.executable_files import is_executable, get_executable_path

name = 'audio_converter_ffmpeg'
version = '0.1.0'

config = {
    'forceFFMpegPath': None,
}

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

    def convert(self, file: str, to_format: str) -> str:
        if not isfile(file):
            raise ValueError(f"{file} не является файлом")

        src_stats = stat(file)
        dst_path = self.get_converted_file_path(file, to_format)

        if isfile(dst_path) and stat(dst_path).st_mtime >= src_stats.st_mtime:
            _logger.debug(
                "Конвертированный файл %s всё ещё актуален, не буду его перезаписывать.",
                dst_path,
            )
            return dst_path

        try:
            command = [
                self._ffmpeg_path,
                '-hide_banner',
                '-y',
                '-i', file,
                dst_path,
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
                dst_path,
                e.output,
            )
            raise ConversionError(
                f"Вызов ffmpeg для конвертирования {file} в {dst_path} завершился с ошибкой (код {e.returncode})"
            )

        return dst_path


def _create_ffmpeg_converter() -> Optional[AudioConverter]:
    ffmpeg_path = _get_ffmpeg_path()

    if ffmpeg_path is not None:
        _logger.debug("Исполняемый файл ffmpeg найден по пути: %s", ffmpeg_path)
        return _AudioConverterImpl(ffmpeg_path)

    _logger.info("Исполняемый файл ffmpeg не найден")

    return None


@step_name('ffmpeg')
def get_audio_converter(nxt, prev, *args, **kwargs):
    prev = prev or _create_ffmpeg_converter()
    return nxt(prev, *args, **kwargs)
