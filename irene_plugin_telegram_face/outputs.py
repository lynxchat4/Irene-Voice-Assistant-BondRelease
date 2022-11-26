from typing import Any, Optional, Iterable

from telebot import TeleBot
from telebot.types import Chat, Message

from irene.brain.abc import TextOutputChannel, AudioOutputChannel
from irene.utils.audio_converter import AudioConverter, ConversionError


def _args_to_send_message(
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
    """
    Канал, отправляющий текстовые сообщения в один чат.
    """

    __slots__ = ('_bot', '_chat')

    def __init__(self, bot: TeleBot, chat: Chat):
        self._bot = bot
        self._chat = chat

    def send(self, text: str, **kwargs):
        self._bot.send_message(
            self._chat.id,
            **_args_to_send_message(text, **kwargs),
        )


class ReplyTextChannel(ChatTextChannel):
    """
    Канал, отправляющий текстовые сообщения в один канал в ответ на заданное сообщение.
    """

    __slots__ = ('_message',)

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


class BroadcastTextChannel(TextOutputChannel):
    """
    Канал, отправляющий текстовые сообщения во все доступные чаты.
    """

    __slots__ = ('_bot', '_chat_ids')

    def __init__(self, bot: TeleBot, chat_ids: Iterable[int]):
        self._bot = bot
        self._chat_ids = chat_ids

    def send(self, text: str, **kwargs):
        args = _args_to_send_message(text, **kwargs)

        sent = False

        for chat_id in self._chat_ids:
            self._bot.send_message(
                chat_id,
                **args,
            )
            sent = True

        if not sent:
            raise Exception("Не удалось отправить сообщение ни в один чат")


class AudioChannel(AudioOutputChannel):
    """
    Канал, отправляющий аудио-файлы в чат.
    """

    __slots__ = ('_bot', '_chat')

    def __init__(
            self,
            bot: TeleBot,
            chat: Chat,
            converter: Optional[AudioConverter] = None,
    ):
        self._bot = bot
        self._chat = chat
        self._converter = converter

    @staticmethod
    def _args_to_telebot(
            alt_text: Optional[str] = None,
            telebot_add_args: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        args = telebot_add_args.copy() if telebot_add_args is not None else {}
        if alt_text is not None:
            args['caption'] = alt_text

        return args

    def send_file(
            self,
            file_path: str,
            **kwargs
    ):
        with open(file_path, 'rb') as file:
            self._bot.send_audio(
                self._chat.id,
                file,
                **self._args_to_telebot(**kwargs),
            )


class VoiceChannel(AudioChannel):
    """
    Канал, отправляющий аудио-файл в виде голосового сообщения.
    """

    __slots__ = ('_converter',)

    def __init__(
            self,
            bot: TeleBot,
            chat: Chat,
            converter: AudioConverter,
    ):
        super().__init__(bot, chat)
        self._converter = converter

    def send_file(
            self,
            file_path: str,
            **kwargs
    ):
        try:
            converted = self._converter.convert(file_path, "ogg")
        except ConversionError:
            return super().send_file(file_path, **kwargs)

        with open(converted, 'rb') as file:
            self._bot.send_voice(
                self._chat.id,
                file,
                **self._args_to_telebot(**kwargs),
            )


class AudioReplyChannel(AudioOutputChannel):
    """
    Канал, отправляющий аудио-файл как ответ на сообщение.
    """

    __slots__ = ('_message', '_channel')

    def __init__(
            self,
            message: Message,
            channel: AudioOutputChannel,
    ):
        self._channel = channel
        self._message = message

    def send_file(self, file_path: str, *, telebot_add_args: Optional[dict[str, Any]] = None, **kwargs):
        telebot_args = telebot_add_args.copy() if telebot_add_args is not None else {}
        telebot_args['reply_to_message_id'] = self._message.id
        self._channel.send_file(file_path, telebot_add_args=telebot_args, **kwargs)
