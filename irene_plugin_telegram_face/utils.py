from telebot import TeleBot  # type: ignore
from telebot.types import Message  # type: ignore


def is_direct_message(message: Message, bot: TeleBot) -> bool:
    """
    Проверяет, адресовано ли данное сообщение напрямую боту.

    Возвращает True если:
    - сообщение отправлено в лс боту
    - сообщение содержит упоминание бота
    - сообщение отправлено в ответ на сообщение бота
    """
    if message.chat.type == 'private':
        return True

    # TODO: Проверить, корректно ли работают следующие проверки
    if message.entities is not None:
        for entity in message.entities:
            if entity.type == 'mention' and entity.user.id == bot.user.id:
                return True

    if (replied := message.reply_to_message) is not None:
        if replied.sender_chat is not None and replied.sender_chat.id == bot.user.id:
            return True
        if replied.from_user is not None and replied.from_user.id == bot.user.id:
            return True

    return False
