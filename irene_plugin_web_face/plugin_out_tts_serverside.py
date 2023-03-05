import threading
from collections import Callable
from logging import getLogger
from typing import Optional, Iterable

from irene.brain.abc import AudioOutputChannel, OutputChannelNotFoundError
from irene.face.abc import FileWritingTTS
from irene.face.tts_helpers import ImmediatePlaybackTTSOutput, FilePlaybackTTS
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import PROTOCOL_OUT_SERVER_SIDE_TTS

_logger = getLogger('serverside-tts')

name = 'plugin_out_tts_serverside'
version = '0.2.0'

config = {
    'ttss': [
        {
            'type': 'silero_v3',
            'model_selector': {
                'gender.female': True,
                'locale.ru': True,
            },
        },
        {
            'type': 'silero_v3',
            'model_selector': {
                'gender.female': True,
                'locale.ru': True,
            },
        },
    ],
}

_tts_mx = threading.Lock()
_ttss: Optional[list[FileWritingTTS]] = None


class _NonFatalError(Exception):
    pass


def _init_ttss(pm: PluginManager) -> list[FileWritingTTS]:
    global _ttss
    if (ttss := _ttss) is not None:
        return ttss

    with _tts_mx:
        if (ttss := _ttss) is not None:
            return ttss

        ttss = []

        for tts_settings in config['ttss']:
            tts = call_all_as_wrappers(
                pm.get_operation_sequence('create_file_tts'),
                None,
                tts_settings,
                pm,
            )

            if tts is not None:
                ttss.append(tts)
            else:
                _logger.warning("Не удалось создать TTS с настройками: %s", tts_settings)

        if len(ttss) > 0:
            _ttss = ttss
            return _ttss

        raise _NonFatalError("Не удалось создать ни один TTS.")


class _ServersideTTSOutput(ProtocolHandler):
    def __init__(self, connection: Connection, ttss: Iterable[FileWritingTTS]):
        try:
            audio_output, = connection.get_associated_outputs().get_channels(AudioOutputChannel)  # type: ignore
        except OutputChannelNotFoundError:
            raise _NonFatalError(
                "не настроен протокол вывода аудио. "
                "Хотя бы один поддерживаемый протокол вывода аудио должен быть указан в списке запрашиваемых "
                "протоколов перед протоколом "
                f"'{PROTOCOL_OUT_SERVER_SIDE_TTS}'."
            )

        for tts in ttss:
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
            prev = prev or _ServersideTTSOutput(connection, _init_ttss(pm))
        except _NonFatalError as e:
            _logger.warning(f"Не удалось настроить серверный TTS: {e}")

    return nxt(prev, proto_name, connection, pm, *args, **kwargs)


def terminate(*_args, **_kwargs):
    global _ttss
    with _tts_mx:
        if _ttss is not None:
            _ttss = None
