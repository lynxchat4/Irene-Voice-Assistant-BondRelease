import re
from importlib.util import spec_from_file_location, module_from_spec
from os.path import abspath, basename, splitext
from re import Pattern
from typing import Optional, Union, Any
from unittest import TestCase

from irene.brain.abc import VAApi, VAContextSource, VAActiveInteractionSource, OutputChannelPool, TextOutputChannel, \
    AudioOutputChannel, InboundMessage
from irene.brain.active_interaction import construct_active_interaction
from irene.brain.context_manager import VAContextManager
from irene.brain.contexts import construct_context
from irene.brain.inbound_messages import PlainTextMessage
from irene.brain.output_pool import OutputPoolImpl


class _VAApiStub(VAApi):
    def __init__(self):
        self._output_log = ''

        api_stub = self

        class TextOutputStub(TextOutputChannel):
            def send(self, text: str, **kwargs):
                api_stub._output_log = re.sub(r' +', ' ', f'{api_stub._output_log} {text}').strip()

        text_out = TextOutputStub()

        class AudioOutputStub(AudioOutputChannel):
            def send_file(self, file_path: str, **kwargs):
                text_out.send(f'[play {abspath(file_path)}]')

        audio_out = AudioOutputStub()

        self._outputs_pool = OutputPoolImpl([text_out, audio_out])

        self.ctx_manager: Optional[VAContextManager] = None

    def get_outputs(self) -> OutputChannelPool:
        return self._outputs_pool

    def get_relevant_outputs(self) -> OutputChannelPool:
        return self._outputs_pool

    def submit_active_interaction(
            self,
            interaction: VAActiveInteractionSource,
            *,
            related_message: Optional[InboundMessage] = None,
    ):
        if self.ctx_manager is None:
            raise AssertionError('submit_active_interaction вызван до using_context')

        self.ctx_manager.process_active_interaction(
            construct_active_interaction(interaction, related_message=related_message)
        )

    def pull_output(self) -> str:
        o = self._output_log
        self._output_log = ''
        return o


_WAIT_PREFIX = "! wait "
_ACT_PREFIX = "! act "


class DialogTestCase(TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ctx_manager: Optional[VAContextManager] = None
        self.va = _VAApiStub()

    def using_context(self, ctx: VAContextSource):
        self.ctx_manager = VAContextManager(self.va, construct_context(ctx))
        self.va.ctx_manager = self.ctx_manager
        self.va.pull_output()

    def say(self, text: str):
        if self.ctx_manager is None:
            raise AssertionError(f'метод say("{text}") вызван до using_context()')

        self.ctx_manager.process_command(PlainTextMessage(text, self.va.get_outputs()))

    @staticmethod
    def expect_playback(file):
        return re.escape(f'[play {abspath(file)}]')

    def assert_reply(self, pattern: Union[str, Pattern]):
        if self.ctx_manager is None:
            raise AssertionError(f'метод assert_reply("{pattern}") вызван до using_context()')

        reply = self.va.pull_output()

        if re.fullmatch(pattern, reply) is None:
            raise AssertionError(
                f'Ожидался ответ, соответствующий шаблону:\n\t"{pattern}"\n' +
                (f'но получен следующий ответ:\n\t"{reply}"' if reply != '' else 'но ответ не получен')
            )

    def delay(self, duration=1.0):
        self.ctx_manager.tick_timeout(duration)

    def play_scenario(self, scenario: str) -> str:
        """
        Проигрывает сценарий диалога с ассистентом, записанный с помощью специального DSL.

        DSL для описания диалогов:

        Каждая строка (line) во входящей строке (string) интерпретируется как отдельная команда, команды выполняются
        последовательно.
        Пробельные символы в начале строки игнорируются, как и строки, не содержащие ничего кроме пробельных символов.

        Доступны следующие команды:

        - ``> текст`` - отправляет текстовое сообщение ассистенту.
            Пробельные символы между ``>`` и началом текста, а так же между концом текста и концом строки (line)
            игнорируются.
        - ``< регулярное выражение`` - ожидает ответа от ассистента и сопоставляет его с образцом.
            Пробельные символы между ``<`` и началом регулярного выражения, а так же между концом регулярного выражения
            и концом строки (line) игнорируются.
            TODO: Придумать что-нибудь чтобы длинные шаблоны можно было переносить на следующую строку.
        - ``! wait (время в секундах)`` - эмитирует ожидание сообщения от пользователя в течение заданного времени
        - ``! act имя_действия`` - начинает активное взаимодействие со стороны ассистента.
            Интерпретатор DSL ищет аттрибут (или метод) ``имя_действия`` в тест-кейсе и создаёт на его основе экземпляр
            VAActiveInteraction.
        - ``# что угодно до конца строки (line)`` - комментарий

        Args:
            scenario:
                сценарий диалога в виде строки
        """
        if self.ctx_manager is None:
            raise AssertionError('метод play_scenario() вызван до using_context()')

        for ln in scenario.split('\n'):
            line = ln.strip()

            if line == '' or line[0] == '#':
                continue
            elif line[0] == '>':
                self.say(line[1:].strip())
            elif line[0] == '<':
                self.assert_reply(line[1:].strip())
            elif line.startswith(_WAIT_PREFIX):
                duration = line[len(_WAIT_PREFIX):]

                self.ctx_manager.tick_timeout(float(duration))
            elif line.startswith(_ACT_PREFIX):
                attr_name = line[len(_ACT_PREFIX):]

                try:
                    interaction = getattr(self, attr_name)
                except AttributeError:
                    raise AssertionError(
                        f'Некорректная команда "{line}": у тесткейса нет аттрибута (или метода) "{attr_name}"')

                interaction = construct_active_interaction(interaction)
                self.ctx_manager.process_active_interaction(interaction)
            else:
                raise AssertionError(f'Некорректная строка в тестовом сценарии:\n\t"{line}"')

        return self.va.pull_output()


class PluginDialogTestCase(DialogTestCase):
    plugin: Any = None

    def setUp(self):
        if self.plugin is None:
            raise AssertionError('плагин для тестирования не выбран')

        if isinstance(self.plugin, str):
            spec = spec_from_file_location(
                splitext(basename(self.plugin))[0],
                abspath(self.plugin),
            )
            plugin = module_from_spec(spec)
            spec.loader.exec_module(plugin)
        else:
            plugin = self.plugin

        manifest = plugin.start(self.va)
        self.using_context(manifest.get('commands'))
