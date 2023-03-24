from telebot import TeleBot
from telebot.types import Message

from irene.brain.abc import OutputChannelPool
from irene.brain.inbound_messages import PlainTextMessage
from irene_plugin_telegram_face.utils import is_direct_message


class TelegramMessage(PlainTextMessage):
    __slots__ = ('message', 'bot')

    def __init__(
            self,
            text: str,
            message: Message,
            bot: TeleBot,
            outputs: OutputChannelPool
    ):
        super().__init__(text, outputs, {'is_direct': is_direct_message(message, bot)})
        self.message = message
        self.bot = bot


class TelegramTextMessage(TelegramMessage):
    __slots__ = ()

    def __init__(
            self,
            message: Message,
            bot: TeleBot,
            outputs: OutputChannelPool
    ):
        super().__init__(
            message.text,
            message,
            bot,
            outputs
        )
