import inspect
from os.path import join, dirname
from typing import Union, Any

from irene import VAContext, construct_context
from irene.brain.command_tree import VACommandTree
from irene.brain.contexts import CommandTreeContext
from irene.plugin_loader.abc import Plugin, PluginManager
from irene.plugin_loader.core_plugins import PluginDiscoveryPlugin
from irene.plugin_loader.magic_plugin import MagicPlugin, step_name
from irene.plugin_loader.plugin_manager import PluginManagerImpl
from irene.plugin_loader.run_operation import call_all
from irene.test_utuls import DialogTestCase


def _get_command_tree(pm: PluginManager) -> VACommandTree[VAContext]:
    tree: VACommandTree[VAContext] = VACommandTree()

    for step in pm.get_operation_sequence('define_commands'):

        definition = step.step

        while True:
            if definition is None:
                break
            elif isinstance(definition, dict):
                tree.add_commands(definition, construct_context)
                break
            elif callable(definition):
                definition = definition()
                continue
            else:
                raise TypeError(
                    f"Неподдерживаемый тип определения команд в плагине {step.plugin} ({step}): {type(definition)}"
                )

    return tree


class _StubRuntime(MagicPlugin):
    """
    Эмитирует деятельность части стандартных плагинов ядра для целей тестирования пользовательских плагинов.
    """

    version = '1.0.0'

    def __init__(
            self,
            configs: dict[str, dict[str, Any]],

    ):
        super().__init__()
        self._configs = configs

    @step_name('config')
    def bootstrap(self, pm: PluginManager, *_args, **_kwargs):
        for step in pm.get_operation_sequence('config'):
            if step.plugin.name in self._configs:
                self._configs[step.plugin.name] = {**step.step, **self._configs[step.plugin.name]}

                if hasattr(step.plugin, 'config'):
                    setattr(step.plugin, 'config', self._configs[step.plugin.name])

        for step in pm.get_operation_sequence('receive_config'):
            if step.plugin.name in self._configs:
                step.step(self._configs[step.plugin.name])

    def plugin_discovered(self, _pm: PluginManager, plugin: Plugin, *_args, **_kwargs):
        for step in plugin.get_operation_steps('config'):
            if plugin.name in self._configs:
                self._configs[step.plugin.name] = {**step.step, **self._configs[step.plugin.name]}

                if hasattr(step.plugin, 'config'):
                    setattr(step.plugin, 'config', self._configs[step.plugin.name])

        for step in plugin.get_operation_steps('receive_config'):
            if step.plugin.name in self._configs:
                step.step(self._configs[step.plugin.name])


class PluginTestCase(DialogTestCase):
    """
    Базовый класс для тесткейсов, загружающих плагины и тестирующих добавляемые ими команды.

    В статическом поле ``plugin`` нужно указать ссылку на экземпляр тестируемого плагина либо путь к его файлу.
    Путь можно указать относительно файла теста, корня пакета (для встроенных плагинов) или папки с пакетами python.

    Конфигурацию можно настроить через статическое поле ``configs``:

        >>> class MyPluginTest(PluginTestCase):
        >>>     plugin = './plugin_my_plugin.py'
        >>>     configs = {
        >>>         'my_plugin': { # имя плагина, как указано в его поле name
        >>>             ...
        >>>         }
        >>>     }

    При старте теста автоматически будет выбран контекст, содержащий все команды, добавленные плагином.
    Далее можно тестировать сценарии диалогов используя DSL из DialogTestCase.
    """

    plugin: Union[str, Plugin]
    configs: dict[str, dict[str, Any]] = {}

    def setUp(self) -> None:
        super().setUp()

        stub_runtime = _StubRuntime(self.configs)
        plugins: list[Plugin] = [stub_runtime]

        test_case_dir = dirname(inspect.getfile(self.__class__))

        if isinstance(self.plugin, Plugin):
            plugins.append(self.plugin)
        elif isinstance(self.plugin, str):
            self.configs['discover_plugins'] = {
                'pluginPaths': [
                    join('{irene_path}', self.plugin),
                    join('{python_path}', self.plugin, 'plugin_*.py'),
                    join(test_case_dir, self.plugin),
                ]
            }
            plugins.append(PluginDiscoveryPlugin())
        else:
            raise AssertionError('В качестве плагина для тестирования передано некорректное значение')

        pm = PluginManagerImpl(plugins)
        self.pm = pm

        call_all(pm.get_operation_sequence('bootstrap'), pm)
        call_all(pm.get_operation_sequence('init'), pm)

        self.using_context(
            CommandTreeContext(_get_command_tree(pm))
        )

    def tearDown(self):
        call_all(self.pm.get_operation_sequence('terminate'), self.pm)
