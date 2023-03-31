import json
import tempfile
import wave
from logging import getLogger
from os.path import join
from typing import Optional, Callable

from telebot import TeleBot  # type: ignore
from telebot.types import Message  # type: ignore
from vosk import Model, KaldiRecognizer  # type: ignore

from irene.brain.abc import InboundMessage, OutputChannel
from irene.brain.output_pool import OutputPoolImpl
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene.utils.audio_converter import AudioConverter, ConversionError
from irene_plugin_telegram_face.inbound_messages import TelegramMessage


class TelegramAudioInputPlugin(MagicPlugin):
    """
    Обеспечивает приём голосовых сообщений из Telegram.

    Использует vosk с моделью, как правило, загруженной плагином `vosk_model_loader`, для распознания речи.
    """

    name = 'telegram_input_audio'
    version = '0.1.0'

    _logger = getLogger(name)

    @staticmethod
    def _get_model(pm: PluginManager) -> Optional[Model]:
        return call_all_as_wrappers(
            pm.get_operation_sequence('get_vosk_model'),
            None,
        )

    @staticmethod
    def _get_audio_converter(pm: PluginManager) -> Optional[AudioConverter]:
        converter: Optional[AudioConverter] = call_all_as_wrappers(
            pm.get_operation_sequence('get_audio_converter'),
            None,
        )

        return converter

    def _recognize_voice(
            self,
            message: Message,
            pm: PluginManager,
            bot: TeleBot,
            converter: AudioConverter
    ) -> Optional[str]:
        model = self._get_model(pm)

        if model is None:
            self._logger.warning(
                "Голосовое сообщение проигнорировано т.к. не удалось загрузить vosk-модель для распознания голоса."
            )
            return None

        with tempfile.TemporaryDirectory() as dir_name:
            tele_file = bot.get_file(message.voice.file_id)
            downloaded_tele_file = bot.download_file(tele_file.file_path)
            temp_src_file_name = join(dir_name, 'voice.ogg')

            with open(temp_src_file_name, 'wb') as f:
                f.write(downloaded_tele_file)

            try:
                temp_dst_file_name = converter.convert(
                    temp_src_file_name, "wav")
            except ConversionError:
                self._logger.exception(
                    "Не удалось преобразовать файл голосового сообщения в формат WAV. "
                    "Сообщение будет проигнорировано.",
                    exc_info=True
                )
                return None

            with wave.Wave_read(temp_dst_file_name) as wav_file:
                recognizer = KaldiRecognizer(model, wav_file.getframerate())

                data = wav_file.readframes(wav_file.getnframes())

        recognizer.AcceptWaveform(data)
        result = json.loads(recognizer.Result())

        return result['text']

    def telegram_add_bot_handlers(
            self,
            bot: TeleBot,
            pm: PluginManager,
            *_args,
            send_message: Callable[[InboundMessage], None],
            **_kwargs
    ):
        if not (converter_ := self._get_audio_converter(pm)):
            self._logger.warning(
                "Приём голосовых сообщений не доступен т.к. не установлен конвертер аудио-файлов."
            )
            return
        else:
            # Давайте поможем MyPy понять, что converter не None после этого if'а
            converter = converter_

        @bot.message_handler(content_types=['voice'])
        def handle_voice_message(message: Message):
            text = self._recognize_voice(message, pm, bot, converter)

            if text is None:
                return

            self._logger.info("Распознано голосовое сообщение \"%s\"", text)

            outputs: list[OutputChannel] = call_all_as_wrappers(
                pm.get_operation_sequence(
                    'telegram_add_message_reply_channels'),
                [],
                message,
                bot,
                pm,
            )

            send_message(TelegramMessage(
                text, message, bot, OutputPoolImpl(outputs)))
