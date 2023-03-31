import unittest

from irene.plugin_loader.abc import OperationStep
from irene.plugin_loader.magic_plugin import MagicPlugin, after, before, operation, step_name, MagicModulePlugin


class MagicPluginTest(unittest.TestCase):
    def test_add_operation_step(self):
        class TestPlugin(MagicPlugin):
            def init(self):
                ...

        plugin = TestPlugin()

        self.assertEqual(
            list(plugin.get_operation_steps('init')),
            [OperationStep(plugin.init, 'TestPlugin.init', plugin, (), ())]
        )

    def test_use_name_override(self):
        class TestPlugin(MagicPlugin):
            name = 'test_plugin'

            def init(self):
                ...

        plugin = TestPlugin()

        self.assertEqual(
            list(plugin.get_operation_steps('init')),
            [OperationStep(plugin.init, 'test_plugin.init', plugin, (), ())]
        )

    def test_step_dependency_decorators(self):
        class TestPlugin(MagicPlugin):
            @after('foo', 'bar')
            @before('buz')
            def init(self):
                ...

        plugin = TestPlugin()

        self.assertEqual(
            list(plugin.get_operation_steps('init')),
            [OperationStep(plugin.init, 'TestPlugin.init',
                           plugin, ('foo', 'bar'), ('buz',))]
        )

    def test_multiple_steps(self):
        class TestPlugin(MagicPlugin):
            @operation('init')
            @after('TestPlugin.init')
            def init2(self):
                ...

            def init(self):
                ...

        plugin = TestPlugin()

        self.assertEqual(
            list(plugin.get_operation_steps('init')),
            [
                OperationStep(plugin.init2, 'TestPlugin.init2',
                              plugin, ('TestPlugin.init',), ()),
                OperationStep(plugin.init, 'TestPlugin.init', plugin, (), ()),
            ]
        )

    def test_step_name_override(self):
        class TestPlugin(MagicPlugin):
            @step_name('init test plugin')
            def init(self):
                ...

        plugin = TestPlugin()

        self.assertEqual(
            list(plugin.get_operation_steps('init')),
            [OperationStep(plugin.init, 'init test plugin', plugin, (), ())]
        )

    def test_decorators_result(self):
        class TestPlugin(MagicPlugin):
            @step_name('renamed step')
            def renamed_step(self) -> str:
                return 'foo'

            @operation('op name override')
            def op_name_override(self) -> str:
                return 'bar'

            @after('dep')
            def step_with_dependencies(self) -> str:
                return 'baz'

            @before('r_dep')
            def step_with_reverse_dependencies(self) -> str:
                return 'buz'

        self.assertEqual(TestPlugin().renamed_step(), 'foo')
        self.assertEqual(TestPlugin().op_name_override(), 'bar')
        self.assertEqual(TestPlugin().step_with_dependencies(), 'baz')
        self.assertEqual(TestPlugin().step_with_reverse_dependencies(), 'buz')

    def test_multiple_ops(self):
        class TestPlugin(MagicPlugin):
            def init(self):
                ...

            def terminate(self):
                ...

        plugin = TestPlugin()

        self.assertEqual(
            list(plugin.get_operation_steps('init')),
            [OperationStep(plugin.init, 'TestPlugin.init', plugin, (), ())],
        )
        self.assertEqual(
            list(plugin.get_operation_steps('terminate')),
            [OperationStep(plugin.terminate,
                           'TestPlugin.terminate', plugin, (), ())],
        )

    def test_ignore_private_and_magic_members(self):
        class TestPlugin(MagicPlugin):
            def _init(self):
                ...

            def __str__(self):
                ...

        plugin = TestPlugin()
        self.assertEqual(
            list(plugin.get_operation_steps('_init')),
            []
        )
        self.assertEqual(
            list(plugin.get_operation_steps('__str__')),
            []
        )

    def test_ignore_plugin_abc_members(self):
        class TestPlugin(MagicPlugin):
            ...

        plugin = TestPlugin()

        self.assertEqual(
            list(plugin.get_operation_steps('get_operation_steps')),
            []
        )
        self.assertEqual(
            list(plugin.get_operation_steps('name')),
            []
        )
        self.assertEqual(
            list(plugin.get_operation_steps('version')),
            []
        )

    def test_module_plugin(self):
        import irene.plugin_loader.tests.magic_plugin_sample as module

        plugin = MagicModulePlugin(module)

        self.assertEqual(plugin.name, 'magic plugin module sample')
        self.assertEqual(plugin.version, '6.6.6')

        self.assertEqual(
            list(plugin.get_operation_steps('init')),
            [OperationStep(
                module.init, 'magic plugin module sample.init', plugin, ('config',), ())]
        )
        self.assertEqual(
            list(plugin.get_operation_steps('terminate')),
            [OperationStep(
                module.terminate, 'magic plugin module sample.terminate', plugin, (), ())]
        )

    def test_module_plugin_attribute_forwarding(self):
        import irene.plugin_loader.tests.magic_plugin_sample as module

        plugin = MagicModulePlugin(module)

        self.assertTrue(hasattr(plugin, 'foo'))

        self.assertIs(module.foo, plugin.foo)

        upd: dict = {}
        plugin.foo = upd
        self.assertIs(module.foo, upd)
        self.assertIs(plugin.foo, upd)


if __name__ == '__main__':
    unittest.main()
