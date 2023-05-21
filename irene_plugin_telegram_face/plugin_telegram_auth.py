from logging import getLogger
from typing import Optional, TypedDict, Iterable

from telebot import TeleBot  # type: ignore
from telebot.types import Message  # type: ignore

from irene.plugin_loader.magic_plugin import MagicPlugin, step_name

LOGIN_COMMAND = '/login'


class TelegramAuthPlugin(MagicPlugin):
    name = 'telegram_auth'
    version = '0.1.0'

    class _Config(TypedDict):
        authorizedChats: list[int]
        authorizationSecret: Optional[str]
        broadcastToAuthorized: bool

    config: _Config = {
        'authorizationSecret': None,
        'authorizedChats': [],
        'broadcastToAuthorized': True,
    }

    config_comment = """
    Настройки авторизации для Telegram-бота.
    
    Доступные параметры:
    - `authorizedChats`       - список id авторизованных чатов.
                                Как правило, не редактируется вручную.
    - `authorizationSecret`   - пароль используемый при следующей авторизации
    - `broadcastToAuthorized` - разрешает рассылку сообщений по всем авторизованным чатам

    ### Добавление авторизованных чатов
    
    По-умолчанию, бот будет игнорировать все входящие сообщения.
    Чтобы бот начал обрабатывать сообщения из чата, чат нужно добавить в список авторизованных чатов.
    Сделать это можно добавив чат в список `authorizedChats` вручную или, более удобно, с помощью следующей процедуры:
    
    1) Записать случайную строку (пароль) в параметр `authorizationSecret`.
       Например,
       
       ```yaml
       authorizationSecret: "password123"
       ```

    2) Отправить боту команду `/login` с паролем.

       > /login password123
    
    Пароль сбрасывается после первого успешного использования.
    Чтобы добавить ещё один чат, процедуру нужно повторить начиная с создания пароля.
    """

    _logger = getLogger(name)

    def _get_authorized_chats(self) -> Iterable[int]:
        """
        Возвращает ``Iterable``, всегда содержащий актуальный список идентификаторов авторизованных чатов.
        """
        me = self

        class AuthorizedChats:
            def __iter__(self):
                return iter(me.config['authorizedChats'])

        return AuthorizedChats()

    @step_name('authorization')
    def telegram_add_bot_handlers(self, bot: TeleBot, *_args, **_kwargs):
        @bot.middleware_handler(update_types=['message'])
        def auth(_bot: TeleBot, message: Message):
            authorized_chats: list = self.config['authorizedChats']

            if message.chat.id in authorized_chats:
                return

            if (text := message.text) is not None and text.startswith(LOGIN_COMMAND):
                self._logger.debug(
                    "Запрос на авторизацию из чата %s (%s)",
                    message.chat.id, message.chat.username,
                )

                auth_secret = self.config['authorizationSecret']

                if auth_secret is not None and auth_secret == text[len(LOGIN_COMMAND):].strip():
                    self._logger.info(
                        "Запрос на авторизацию из чата %s (%s) одобрен",
                        message.chat.id, message.chat.username,
                    )

                    authorized_chats.append(message.chat.id)
                    self.config['authorizedChats'] = authorized_chats
                    self.config['authorizationSecret'] = None

                    bot.send_message(
                        message.chat.id,
                        "Доступ предоставлен",
                        reply_to_message_id=message.message_id,
                    )

                    # Выкидываем исключение несмотря на успех, чтобы ассистент не пытался обрабатывать сообщение
                    # с запросом на авторизацию как команду.
                    raise Exception(f"Предоставлен доступ чату {message.chat.id} ({message.chat.username})")

            bot.send_message(
                message.chat.id,
                "Доступ запрещён",
                reply_to_message_id=message.message_id,
            )
            raise Exception(
                f"Получено сообщение из неавторизованного чата {message.chat.id} ({message.chat.username})"
            )

    def telegram_get_broadcast_chats(self, nxt, prev, *args, **kwargs):
        if self.config['broadcastToAuthorized']:
            prev = self._get_authorized_chats()
        return nxt(prev, *args, **kwargs)
