from typing import Callable, Optional, Any

from irene.brain.abc import OutputChannel, AudioOutputChannel
from irene.face.abc import ImmediatePlaybackTTS, FileWritingTTS
from irene.face.mute_group import NULL_MUTE_GROUP
from irene.face.tts_helpers import ImmediatePlaybackTTSOutput, FilePlaybackTTS
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers

name = 'plugin_local_output_tts'
version = '0.1.0'


def create_local_output(
        nxt: Callable,
        prev: Optional[OutputChannel],
        pm: PluginManager,
        settings: dict[str, Any],
        *args,
        **kwargs
):
    requested_type = settings.get('type')

    if prev is None:
        if requested_type == 'tts-immediate':
            immediate_tts: Optional[ImmediatePlaybackTTS] = call_all_as_wrappers(
                pm.get_operation_sequence('create_immediate_tts'),
                None,
                settings.get('tts', {}),
                pm,
            )

            if immediate_tts is None:
                raise Exception("Не удалось создать TTS")

            prev = ImmediatePlaybackTTSOutput(
                immediate_tts,
                mute_group=kwargs.get('mute_group', NULL_MUTE_GROUP),
            )
        elif requested_type == 'tts-file':
            file_tts: Optional[FileWritingTTS] = call_all_as_wrappers(
                pm.get_operation_sequence('create_file_tts'),
                None,
                settings.get('tts', {}),
                pm,
            )

            if file_tts is None:
                raise Exception("Не удалось создать TTS")

            player = call_all_as_wrappers(
                pm.get_operation_sequence('create_local_output'),
                None,
                pm,
                settings.get('player', {}),
                *args,
                **kwargs,
            )

            if not isinstance(player, AudioOutputChannel):
                raise Exception("Не удалось создать канал для воспроизведения")

            prev = ImmediatePlaybackTTSOutput(
                FilePlaybackTTS(file_tts, player),
                mute_group=kwargs.get('mute_group', NULL_MUTE_GROUP),
            )

    return nxt(prev, pm, settings, *args, **kwargs)
