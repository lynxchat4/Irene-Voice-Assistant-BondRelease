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


class TelegramFacePlugin(MagicPlugin):
    """
    Обеспечивает взаимодействие с ассистентом через Telegram-бота.
    """

    name = 'face_telegram'
    version = '0.2.0'

    config_comment = """
    Настройки Telegram-бота.
    
    Доступные параметры:
    - `token`               - токен бота.
                              Для создания бота и получения токена обращайтесь к https://t.me/BotFather.
                              После изменения токена, для его использования требуется перезапуск приложения.
    """

    class _Config(TypedDict):
        token: Optional[str]
        numThreads: int

    config: _Config = {
        "token": None,
        "numThreads": 2,
    }

    _logger = getLogger(name)

    def __init__(self) -> None:
        super().__init__()

        self._bot: Optional[TeleBot] = None
        self._pm: Optional[PluginManager] = None

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

        broadcast_chats: Optional[Iterable[int]] = call_all_as_wrappers(
            pm.get_operation_sequence('telegram_get_broadcast_chats'),
            None,
            pm,
        )
        broadcast_channels: list[OutputChannel] = []

        if broadcast_chats is not None:
            broadcast_channels = call_all_as_wrappers(
                pm.get_operation_sequence('telegram_create_broadcast_channels'),
                broadcast_channels,
                bot, broadcast_chats, pm,
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
