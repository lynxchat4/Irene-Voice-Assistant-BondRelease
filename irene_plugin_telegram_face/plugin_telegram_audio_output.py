from logging import getLogger
from typing import Optional

from telebot import TeleBot
from telebot.types import Message

from irene.brain.abc import OutputChannel, AudioOutputChannel
from irene.face.tts_helpers import FilePlaybackTTS, ImmediatePlaybackTTSOutput
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin, step_name, before
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene.utils.audio_converter import AudioConverter
from irene_plugin_telegram_face.outputs import AudioChannel, AudioReplyChannel, VoiceChannel


class TelegramAudioOutputPlugin(MagicPlugin):
    """
    Обеспечивает отправку аудио-файлов и текста, озвученного через TTS в Telegram.
    """
    name = 'telegram_output_audio'
    version = '0.2.0'

    _logger = getLogger(name)

    config_comment = """
    Настройки отправки аудио в Telegram.
    
    Доступные параметры:
    - `replyInPrivate`        - слать сообщения как ответы в приватных чатах
    - `replyInGroups`         - слать сообщения как ответы в групповых чатах
    - `trySendVoice`          - пытаться отправлять аудио как голосовые сообщения.
                                Это может не получиться если не доступен конвертер аудио-файлов или файлы не удаётся
                                преобразовывать в формат OGG.
                                Когда звуки не отправляются как голосовые сообщения, они отправляются как аудио-записи.
    - `voiceProfileSelector`  - селектор, определяющий, какие голоса будут использоваться при озвучении текстовых
                                сообщений.
    """

    config = {
        'replyInPrivate': False,
        'replyInGroups': True,
        'trySendVoice': True,
        'voiceProfileSelector': {},
    }

    @staticmethod
    def _get_audio_converter(pm: PluginManager) -> Optional[AudioConverter]:
        converter: Optional[AudioConverter] = call_all_as_wrappers(
            pm.get_operation_sequence('get_audio_converter'),
            None,
        )

        return converter

    @step_name('audio')
    @before('plaintext')
    def telegram_add_message_reply_channels(
            self,
            nxt,
            channels: list[OutputChannel],
            message: Message,
            bot: TeleBot,
            pm: PluginManager,
            *args,
            **kwargs
    ):
        converter: Optional[AudioConverter] = None

        if self.config['trySendVoice']:
            converter = self._get_audio_converter(pm)

        if converter is None:
            audio_channel: AudioOutputChannel = AudioChannel(bot, message.chat)
        else:
            audio_channel = VoiceChannel(bot, message.chat, converter)

        send_reply = self.config['replyInPrivate' if message.chat.type == 'private' else 'replyInGroups']

        if send_reply:
            audio_channel = AudioReplyChannel(message, audio_channel)

        ttss = call_all_as_wrappers(
            pm.get_operation_sequence('get_file_writing_tts_engines'),
            [],
            pm,
            selector=self.config['voiceProfileSelector'],
        )

        if len(ttss) == 0:
            self._logger.info("Не удалось получить ни одного TTS")

        for tts in ttss:
            immediate_tts = FilePlaybackTTS(tts, audio_channel)
            channels.append(ImmediatePlaybackTTSOutput(immediate_tts))

        channels.append(audio_channel)

        return nxt(channels, message, bot, pm, *args, **kwargs)

    # TODO: Add broadcasts (?)
    # def telegram_create_broadcast_channels(
    #         self,
    #         nxt,
    #         channels: list[OutputChannel],
    #         bot: TeleBot,
    #         authorized_chats: Iterable[int],
    #         *args,
    #         **kwargs
    # ):
    #     ...
    #     return nxt(channels, bot, authorized_chats, *args, **kwargs)
