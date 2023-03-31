import contextlib
import json
from logging import getLogger
from queue import Queue
from typing import Any, Optional, Callable, Iterable, TypedDict

import sounddevice  # type: ignore

from irene.face.abc import LocalInput, Muteable, MuteGroup
from irene.face.mute_group import NULL_MUTE_GROUP
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers

name = 'local_input_sounddevice_vosk'
version = '0.1.0'


class _Config(TypedDict):
    deviceId: Optional[int]
    sampleRate: Optional[int]


config: _Config = {
    'deviceId': None,
    'sampleRate': None,
}

config_comment = f"""
Настройки локального голосового ввода через sounddevice с распознанием через vosk.

Доступные параметры:
- `deviceId`      - номер устройства ввода (микрофона) которое будет использовано для прослушивания голосовых команд.
                    См. список устройств далее.
                    Если `null`, то будет использоваться устройство по-умолчанию.
- `sampleRate`    - частота дискретизации ввода.
                    Если `null`, то будет использоваться частота по-умолчанию для выбранного устройства.

Для применения любых изменений требуется перезапуск приложения.

Доступные устройства:
{sounddevice.query_devices()}
"""

_logger = getLogger(name)


class _VoskSoundDeviceInput(LocalInput, Muteable):
    def __init__(self, pm: PluginManager, mute_group: MuteGroup):
        self._device_id = config['deviceId']
        self._device_info = sounddevice.query_devices(self._device_id, 'input')
        self._sample_rate: int = int(config['sampleRate']) if config['sampleRate'] is not None \
            else self._device_info['default_samplerate']

        self._model = call_all_as_wrappers(
            pm.get_operation_sequence('get_vosk_model'),
            None,
        )

        if self._model is None:
            raise Exception("Не удалось получить модель для vosk")

        self._mg = mute_group

        self._muted = False
        self._stream: Optional[sounddevice.RawInputStream] = None

    @contextlib.contextmanager
    def run(self):
        import vosk  # type: ignore

        queue = Queue()
        aborted = False

        def _stream_callback(data, _frames, _time, status):
            if status:
                _logger.debug('input stream callback flags: %s',
                              status)  # ¯\_(ツ)_/¯
            if not self._muted:
                queue.put(bytes(data))

        recognizer = vosk.KaldiRecognizer(self._model, self._sample_rate)

        self._stream = sounddevice.RawInputStream(
            self._sample_rate,
            blocksize=8000,
            device=self._device_id,
            dtype='int16',
            channels=1,
            callback=_stream_callback,
        )

        def _read_commands() -> Iterable[str]:
            while True:
                msg = queue.get()

                if msg is None or aborted:
                    return
                elif self._muted:
                    pass
                elif recognizer.AcceptWaveform(msg):
                    recognized = json.loads(recognizer.Result())
                    text = recognized['text']

                    if len(text) > 0:
                        _logger.debug("Распознано: %s", text)

                        yield text

        def _abort():
            nonlocal aborted
            aborted = True
            queue.put(None)

        remove_from_mg = self._mg.add_item(self)

        try:
            with self._stream:
                yield _read_commands(), _abort
        finally:
            self._stream = None
            remove_from_mg()

    def mute(self):
        _logger.debug("Muting..")
        self._muted = True
        if self._stream is not None and not self._stream.stopped:
            self._stream.abort()

    def unmute(self):
        _logger.debug("Unmuting..")
        self._muted = False
        if self._stream is not None and self._stream.stopped:
            self._stream.start()


def create_local_input(
        nxt: Callable,
        prev: Optional[LocalInput],
        pm: PluginManager,
        settings: dict[str, Any],
        *args,
        **kwargs
):
    if settings.get('type') == 'vosk+sounddevice':
        try:
            prev = prev if prev is not None else _VoskSoundDeviceInput(
                pm,
                mute_group=kwargs.get('mute_group', NULL_MUTE_GROUP),
            )
        except sounddevice.PortAudioError as e:
            _logger.error("Не удалось инициализировать portaudio: %s", e)

    return nxt(prev, pm, settings, *args, **kwargs)
