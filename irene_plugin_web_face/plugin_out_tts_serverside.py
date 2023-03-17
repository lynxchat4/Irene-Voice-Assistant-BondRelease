from collections import Callable
from logging import getLogger
from typing import Optional, Iterable, Any

from irene.brain.abc import AudioOutputChannel, OutputChannelNotFoundError
from irene.face.abc import FileWritingTTS
from irene.face.tts_helpers import ImmediatePlaybackTTSOutput, FilePlaybackTTS
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene_plugin_web_face.abc import Connection, ProtocolHandler
from irene_plugin_web_face.protocol import PROTOCOL_OUT_SERVER_SIDE_TTS

name = 'plugin_out_tts_serverside'
version = '0.3.0'

_logger = getLogger(name)

config: dict[str, Any] = {
    'profile_selector': {},
}


class _NonFatalError(Exception):
    pass


def _init_ttss(pm: PluginManager) -> list[FileWritingTTS]:
    ttss = call_all_as_wrappers(
        pm.get_operation_sequence('get_file_writing_tts_engines'),
        [],
        pm,
        selector=config['profile_selector'],
    )

    if len(ttss) == 0:
        raise _NonFatalError(
            "Не удалось получить ни один TTS. Проверьте настройки профилей TTS (voice_profiles) и селектор "
            "(profile_selector) в настройках плагина plugin_out_tts_serverside."
        )

    return ttss


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
