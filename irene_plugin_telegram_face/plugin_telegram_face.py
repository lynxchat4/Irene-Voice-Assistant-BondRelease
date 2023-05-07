from logging import getLogger
from typing import Optional, Iterable, TypedDict

import telebot.apihelper as apihelper  # type: ignore
from telebot import TeleBot
from telebot.types import Message  # type: ignore

from irene.brain.abc import Brain, OutputChannel
from irene.brain.output_pool import OutputPoolImpl
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin
from irene.plugin_loader.run_operation import call_all_as_wrappers, call_all

apihelper.ENABLE_MIDDLEWARE = True

LOGIN_COMMAND = '/login'


class TelegramFacePlugin(MagicPlugin):
    """
    Обеспечивает взаимодействие с ассистентом через Telegram-бота.
    """

    name = 'face_telegram'
    version = '0.1.0'

    config_comment = """
    Настройки Telegram-бота.
    
    Доступные параметры:
    - `token`               - токен бота.
                              Для создания бота и получения токена обращайтесь к https://t.me/BotFather.
                              После изменения токена, для его использования требуется перезапуск приложения.
    - `authorizedChats`     - список id авторизованных чатов.
                              Как правило, не редактируется вручную.
    - `authorizationSecret` - пароль используемый при следующей авторизации
    
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

    class _Config(TypedDict):
        token: Optional[str]
        authorizedChats: list[int]
        authorizationSecret: Optional[str]
        numThreads: int

    config: _Config = {
        "token": None,
        "authorizedChats": [],
        "authorizationSecret": None,
        "numThreads": 2,
    }

    _logger = getLogger(name)

    def __init__(self):
        super().__init__()

        self._bot: Optional[TeleBot] = None
        self._pm: Optional[PluginManager] = None

    def _get_authorized_chats(self) -> Iterable[int]:
        """
        Возвращает ``Iterable``, всегда содержащий актуальный список идентификаторов авторизованных чатов.
        """
        me = self

        class AuthorizedChats:
            def __iter__(self):
                return iter(me.config['authorizedChats'])

        return AuthorizedChats()

    def telegram_add_bot_handlers(self, bot: TeleBot, *_args, **_kwargs):
        @bot.middleware_handler(update_types=['message'])
        def auth(_bot: TeleBot, message: Message):
            authorized_chats: list = self.config.get('authorizedChats', [])

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
                    return

                bot.send_message(
                    message.chat.id,
                    "Доступ запрещён",
                    reply_to_message_id=message.message_id,
                )
                raise Exception(
                    f"Получено сообщение из неавторизованного чата {message.chat.id} ({message.chat.username})"
                )

    def run(self, pm: PluginManager, *_args, **_kwargs):
        token: Optional[str] = self.config['token']

        if token is None:
            self._logger.warning(
                "Токен для телеграм-бота не установлен. Бот не будет запущен. "
                "Добавьте токен и перезапустите приложения для запуска бота."
            )
            return

        bot = TeleBot(
            token,
            suppress_middleware_excepions=True,
            num_threads=self.config['numThreads'],
        )

        brain: Brain = call_all_as_wrappers(
            pm.get_operation_sequence('get_brain'), None, pm)

        if brain is None:
            raise Exception("Не удалось найти мозг.")

        broadcast_channels: list[OutputChannel] = call_all_as_wrappers(
            pm.get_operation_sequence('telegram_create_broadcast_channels'),
            [],
            bot,
            self._get_authorized_chats(),
            pm,
        )

        with brain.send_messages(OutputPoolImpl(broadcast_channels)) as send_message:
            call_all(
                pm.get_operation_sequence('telegram_add_bot_handlers'),
                bot, pm,
                send_message=send_message,
            )

            self._bot = bot
            bot.infinity_polling()

    def terminate(self, *_args, **_kwargs):
        if self._bot is not None:
            self._bot.stop_bot()
