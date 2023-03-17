from logging import getLogger
from typing import Callable, Any

import sounddevice
import soundfile

from irene.brain.abc import OutputChannel, AudioOutputChannel
from irene.plugin_loader.abc import PluginManager

name = 'local_output_sounddevice'
version = '0.1.0'

config = {
    'deviceId': None,
    'blockSize': 1024,
    'postPlaySleepMS': 250,
}

config_comment = f"""
Настройки вывода аудио через библиотеку sounddevice.

Доступные параметры:
- `deviceId`          - номер устройства вывода которое будет использовано для вывода звука.
                        См. список устройств далее.
                        Если `null`, то будет использоваться устройство по-умолчанию.
- `blockSize`         - размер (в фреймах/сэмплах) буфера, используемого при воспроизведении.
- `postPlaySleepMS`   - длительность (в миллисекундах) задержки добавляемой перед закрытием потока вывода.
                        Это необходимо для обхода бага в библиотеке portaudio, проявляющегося на некоторых платформах.
                        С.м. https://github.com/spatialaudio/python-sounddevice/issues/283.
                        Если на Вашем устройстве возникают заметные задержки между завершением воспроизведения и началом
                        следующего действия (воспроизведения следующей фразы или ожидания новых команд), то попробуйте
                        установить этот параметр в 0.
                        Если наоборот, наблюдается "проглатывание" окончаний фраз, то попробуйте увеличить значение
                        параметра.

Изменения применяются при следующем воспроизведении после их загрузки. Перезапуск приложения не требуется.

Доступные устройства:
{sounddevice.query_devices()}
"""

_logger = getLogger(name)


class _SoundDeviceAudioOutput(AudioOutputChannel):
    def check(self):
        sounddevice.query_devices(config['deviceId'], 'output')

        return self

    def send_file(self, file_path: str, **kwargs):
        _logger.debug("Собираюсь воспроизводить файл %s", file_path)

        block_size = config['blockSize']
        no_buffering = block_size is None or block_size <= 0

        with soundfile.SoundFile(file_path) as sf:
            with sounddevice.RawOutputStream(
                    samplerate=sf.samplerate,
                    device=config['deviceId'],
                    channels=sf.channels,
                    dtype='float32',
                    blocksize=None if no_buffering else block_size,
            ) as stream:
                while len(buf := sf.buffer_read(-1 if no_buffering else block_size, 'float32')) > 0:
                    stream.write(buf)

                if sleepMs := config['postPlaySleepMS']:
                    sounddevice.sleep(sleepMs)


def create_local_outputs(
        nxt: Callable,
        prev: list[OutputChannel],
        pm: PluginManager,
        settings: dict[str, Any],
        *args,
        **kwargs
):
    if settings.get('type') == 'sounddevice':
        try:
            prev.append(_SoundDeviceAudioOutput().check())
        except sounddevice.PortAudioError as e:
            _logger.error("Не удалось инициализировать portaudio: %s", e)

    return nxt(prev, pm, settings, *args, **kwargs)
