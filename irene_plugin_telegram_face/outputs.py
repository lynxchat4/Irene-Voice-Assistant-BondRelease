from typing import Any, Optional

from telebot import TeleBot
from telebot.types import Chat, Message

from irene.brain.abc import TextOutputChannel, AudioOutputChannel


def args_to_send_message(
        text: str,
        text_html: Optional[str] = None,
        text_markdown: Optional[str] = None,
        telebot_add_args: Optional[dict[str, Any]] = None,
        **_kwargs
) -> dict[str, Any]:
    args = telebot_add_args.copy() if telebot_add_args is not None else {}

    if text_html is not None:
        args['text'] = text_html
        args['parse_mode'] = 'HTML'
    elif text_markdown is not None:
        args['text'] = text_markdown
        args['parse_mode'] = 'MarkdownV2'
    else:
        args['text'] = text

    return args


class ChatTextChannel(TextOutputChannel):
    def __init__(self, bot: TeleBot, chat: Chat):
        self._bot = bot
        self._chat = chat

    def send(self, text: str, **kwargs):
        self._bot.send_message(
            self._chat.id,
            **args_to_send_message(text, **kwargs),
        )


class ReplyTextChannel(ChatTextChannel):
    def __init__(self, bot: TeleBot, message: Message):
        super().__init__(bot, message.chat)
        self._message = message

    def send(
            self,
            text: str,
            *,
            telebot_add_args: Optional[dict[str, Any]] = None,
            **kwargs
    ):
        telebot_add_args = telebot_add_args.copy() if telebot_add_args is not None else {}
        telebot_add_args['reply_to_message_id'] = self._message.id
        super().send(text, telebot_add_args=telebot_add_args, **kwargs)


class AudioChannel(AudioOutputChannel):
    def __init__(self, bot: TeleBot, chat: Chat):
        self._bot = bot
        self._chat = chat

    def send_file(
            self,
            file_path: str,
            *,
            alt_text: Optional[str] = None,
            telebot_add_args: Optional[dict[str, Any]] = None,
            **kwargs
    ):
        raise NotImplemented
