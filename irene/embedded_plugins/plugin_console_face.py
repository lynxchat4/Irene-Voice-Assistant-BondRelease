from irene.brain.abc import TextOutputChannel
from irene.brain.inbound_messages import PlainTextMessage
from irene.brain.output_pool import OutputPoolImpl
from irene.plugin_loader.magic_plugin import MagicPlugin
from irene.plugin_loader.plugins_abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers


class ConsoleOutputChannel(TextOutputChannel):
    def __init__(self, prefix):
        self.prefix = prefix

    def send(self, text: str, **kwargs):
        print(self.prefix + text)


class ConsoleFace(MagicPlugin):
    name = 'face_console'
    version = '1.0.0'

    config = {
        'enabled': False,
        'prompt': '> ',
        'reply_prefix': '< ',
    }

    def __init__(self):
        super().__init__()
        self._outputs = None

    def init(self, *_args, **_kwargs):
        self._outputs = OutputPoolImpl((
            ConsoleOutputChannel(self.config.get('reply_prefix', '< ')),
        ))

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

                send_message(PlainTextMessage(text, self._outputs))
