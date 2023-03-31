from typing import Callable, Iterable

from telebot import TeleBot  # type: ignore
from telebot.types import Message  # type: ignore

from irene.brain.abc import InboundMessage, OutputChannel
from irene.brain.output_pool import OutputPoolImpl
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin, step_name
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene_plugin_telegram_face.inbound_messages import TelegramTextMessage
from irene_plugin_telegram_face.outputs import ReplyTextChannel, ChatTextChannel, BroadcastTextChannel


class TelegramPlaintextIOPlugin(MagicPlugin):
    """
    Обеспечивает приём и отправку текстовых сообщений через Telegram.
    """

    name = 'telegram_io_plaintext'
    version = '0.1.0'

    config_comment = """
    Настройки приёма и отправки текстовых сообщений через Telegram.

    Доступны следующие параметры:
    - `replyInPrivate`  - слать сообщения как ответы в приватных чатах
    - `replyInGroups`   - слать сообщения как ответы в групповых чатах
    - `enableBroadcast` - позволяет боту рассылать сообщения по всем доступным чатам.
                          Для применения изменений этого параметра нужен перезапуск приложения.
    """

    config = {
        'replyInPrivate': False,
        'replyInGroups': True,
        'enableBroadcast': False,
    }

    def telegram_create_broadcast_channels(
            self,
            nxt,
            channels: list[OutputChannel],
            bot: TeleBot,
            authorized_chats: Iterable[int],
            *args,
            **kwargs
    ):
        if self.config['enableBroadcast']:
            channels.append(BroadcastTextChannel(bot, authorized_chats))

        return nxt(channels, bot, authorized_chats, *args, **kwargs)

    @step_name('plaintext')
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
        send_reply = self.config['replyInPrivate' if message.chat.type ==
                                                     'private' else 'replyInGroups']

        if send_reply:
            channels.append(ReplyTextChannel(bot, message))
        else:
            channels.append(ChatTextChannel(bot, message.chat))

        return nxt(channels, message, bot, pm, *args, **kwargs)

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
            outputs: list[OutputChannel] = call_all_as_wrappers(
                pm.get_operation_sequence(
                    'telegram_add_message_reply_channels'),
                [],
                message,
                bot,
                pm,
            )

            send_message(
                TelegramTextMessage(message, bot, OutputPoolImpl(outputs))
            )
