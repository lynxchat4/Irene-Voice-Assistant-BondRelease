from typing import Callable, Optional, Mapping, Any

from irene.brain.abc import TextOutputChannel, VAContext, VAApi, InboundMessage
from irene.brain.contexts import BaseContextWrapper
from irene.brain.inbound_messages import PlainTextMessage
from irene.brain.output_pool import OutputPoolImpl
from irene.constants.labels import pure_text_channel_labels
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.magic_plugin import MagicPlugin, before, operation, after
from irene.plugin_loader.run_operation import call_all_as_wrappers


class ConsoleOutputChannel(TextOutputChannel):
    def __init__(self, prefix):
        self.prefix = prefix

    def send(self, text: str, **kwargs):
        print(self.prefix + text)

    @property
    def meta(self) -> Mapping[str, Any]:
        return pure_text_channel_labels()


class ConsoleMessage(PlainTextMessage):
    pass


class ConsoleFace(MagicPlugin):
    """
    Предоставляет текстовый консольный интерфейс для взаимодействия с ассистентом.

    Если плагин загружен и включён (поле `enabled` в конфиге) то процесс принимает команды из стандартного потока ввода
    и отвечает через стандартный поток вывода.
    Предназначен в первую очередь для отладки и ручного тестирования сценариев диалогов.

    Использование плагина может приводить к нештатному завершению работы приложения при получении сигнала прерывания.
    """

    name = 'face_console'
    version = '1.0.0'

    config = {
        'enabled': False,
        'skipTriggerPhrase': False,
        'prompt': '> ',
        'reply_prefix': '< ',
    }

    config_comment = """
    Настройки консольного текстового интерфейса.

    Доступные параметры:
    - `enabled`                 - включает текстовый консольный интерфейс
    - `skipTriggerPhrase`       - если установлен в true, консольный интерфейс не требует использования имени ассистента
                                  для запуска команд
    - `prompt`, `reply_prefix`  - префиксы вводимых пользователем команд и ответов ассистента
    """

    def __init__(self):
        super().__init__()
        self._outputs = None

    def init(self, *_args, **_kwargs):
        self._outputs = OutputPoolImpl((
            ConsoleOutputChannel(self.config.get('reply_prefix', '< ')),
        ))

    @operation('create_root_context')
    @before('add_trigger_phrase')
    @after('load_commands')
    def skip_trigger_phrase(
            self,
            nxt: Callable,
            prev: Optional[VAContext],
            *args, **kwargs,
    ):
        if prev is None:
            raise ValueError()

        if not self.config['skipTriggerPhrase']:
            return nxt(prev, *args, **kwargs)

        class TriggerPhraseSkipContext(BaseContextWrapper):
            def handle_command(self, va: VAApi, message: InboundMessage) -> Optional[VAContext]:
                if isinstance(message.get_original(), ConsoleMessage):
                    return prev.handle_command(va, message)

                return super().handle_command(va, message)

        return TriggerPhraseSkipContext(
            nxt(prev, *args, **kwargs)
        )

    def run(self, pm: PluginManager, *_args, **_kwargs):
        if not self.config.get('enabled', False):
            return

        brain = call_all_as_wrappers(pm.get_operation_sequence('get_brain'), None, pm)

        if brain is None:
            raise Exception("Не удалось найти мозг.")

        with brain.send_messages(self._outputs) as send_message:
            while True:
                try:
                    text = input(self.config.get('prompt', '> '))
                except EOFError:
                    print("\nКонсольный поток ввода завершён.")
                    break

                send_message(ConsoleMessage(text, self._outputs))
