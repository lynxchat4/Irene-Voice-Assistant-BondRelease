from typing import Callable

from telebot import TeleBot
from telebot.types import Message

from irene.brain.abc import InboundMessage
from irene.brain.inbound_messages import PlainTextMessage
from irene.brain.output_pool import OutputPoolImpl
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin
from irene_plugin_telegram_face.utils import is_direct_message


class TelegramPlaintextInputPlugin(MagicPlugin):
    name = 'telegram_input_plaintext'
    version = '0.1.0'

    def telegram_add_bot_handlers(
            self,
            bot: TeleBot,
            pm: PluginManager,
            *_args,
            send_message: Callable[[InboundMessage], None],
            **_kwargs
    ):
        @bot.message_handler(content_types=['text'])
        def handle_text_message(message: Message):
            outputs = OutputPoolImpl(())

            if is_direct_message(message, bot):
                ...
            else:
                return send_message(PlainTextMessage(message.text, outputs))
