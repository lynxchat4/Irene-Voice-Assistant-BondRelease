import threading
from collections import Callable
from logging import getLogger
from typing import Optional

from irene.brain.abc import AudioOutputChannel, OutputChannelNotFoundError
from irene.face.abc import FileWritingTTS
from irene.face.tts_helpers import ImmediatePlaybackTTSOutput, FilePlaybackTTS
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import PROTOCOL_OUT_SERVER_SIDE_TTS

_logger = getLogger('serverside-tts')

name = 'plugin_out_tts_serverside'
version = '0.1.0'

config = {
    'tts': {
        'type': 'silero_v3',
    },
}

_tts_mx = threading.Lock()
_tts: Optional[FileWritingTTS] = None


class _NonFatalError(Exception):
    pass


def _init_tts(pm: PluginManager) -> FileWritingTTS:
    global _tts
    if (tts := _tts) is not None:
        return tts

    with _tts_mx:
        if (tts := _tts) is not None:
            return tts

        _tts = call_all_as_wrappers(
            pm.get_operation_sequence('create_file_tts'),
            None,
            config['tts'],
            pm,
        )

        if _tts is None:
            raise _NonFatalError(
                "не удалось создать TTS. "
                f"Проверьте настройки плагина {name}."
            )

        return _tts


class _ServersideTTSOutput(ProtocolHandler):
    def __init__(self, connection: Connection, tts: FileWritingTTS):
        try:
            audio_output, = connection.get_associated_outputs().get_channels(AudioOutputChannel)  # type: ignore
        except OutputChannelNotFoundError:
            raise _NonFatalError(
                "не настроен протокол вывода аудио. "
                "Хотя бы один поддерживаемый протокол вывода аудио должен быть указан в списке запрашиваемых "
                "протоколов перед протоколом "
                f"'{PROTOCOL_OUT_SERVER_SIDE_TTS}'."
            )

        connection.register_output(
            ImmediatePlaybackTTSOutput(
                FilePlaybackTTS(
                    tts,
                    audio_output,
                )
            )
        )

    def start(self):
        pass

    def terminate(self):
        pass


def init_client_protocol(
        nxt: Callable,
        prev: Optional[ProtocolHandler],
        proto_name: str,
        connection: Connection,
        pm: PluginManager,
        *args,
        **kwargs):
    if proto_name == PROTOCOL_OUT_SERVER_SIDE_TTS:
        try:
            prev = prev or _ServersideTTSOutput(connection, _init_tts(pm))
        except _NonFatalError as e:
            _logger.warning(f"Не удалось настроить серверный TTS: {e}")

    return nxt(prev, proto_name, connection, pm, *args, **kwargs)


def terminate(*_args, **_kwargs):
    global _tts
    with _tts_mx:
        if (tts := _tts) is not None:
            _tts = None
            tts.terminate()
