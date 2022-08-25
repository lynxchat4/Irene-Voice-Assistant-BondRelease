import unittest
from logging import Logger
from unittest.mock import Mock

from irene.plugin_loader.abc import OperationStep, DependencyCycleException
from irene.plugin_loader.magic_plugin import MagicPlugin, after, step_name, before
from irene.plugin_loader.plugin_manager import PluginManagerImpl


class _TestPlugin1(MagicPlugin):
    def init(self):
        ...


class _TestPlugin2(MagicPlugin):
    @after('_TestPlugin1.init')
    def init(self):
        ...


class _TestPlugin3(MagicPlugin):
    @before('_TestPlugin1.init')
    def init(self):
        ...


class _ChickenPlugin(MagicPlugin):
    @after('egg')
    @step_name('chicken')
    def create(self):
        ...


class _EggPlugin(MagicPlugin):
    @after('chicken')
    @step_name('egg')
    def create(self):
        ...


class PluginManagerTest(unittest.TestCase):
    def test_get_single_step(self):
        logger = Mock(spec=Logger)
        plugins = [_TestPlugin1()]
        pm = PluginManagerImpl(plugins, logger=logger)

        self.assertEqual(
            list(pm.get_operation_sequence('init')),
            [OperationStep(plugins[0].init, '_TestPlugin1.init', plugins[0], (), ())]
        )

        logger.warning.assert_not_called()

    def test_ignore_duplicates(self):
        logger = Mock(spec=Logger)
        plugins = [_TestPlugin1(), _TestPlugin1()]
        pm = PluginManagerImpl(plugins, logger=logger)

        self.assertEqual(
            list(pm.get_operation_sequence('init')),
            [OperationStep(plugins[0].init, '_TestPlugin1.init', plugins[0], (), ())]
        )

        logger.warning.assert_called_once()

    def test_detect_loop(self):
        pm = PluginManagerImpl([_ChickenPlugin(), _EggPlugin()])

        with self.assertRaises(DependencyCycleException) as e:
            pm.get_operation_sequence('create')

        self.assertRegex(str(e.exception), r'_ChickenPlugin')
        self.assertRegex(str(e.exception), r'_EggPlugin')
        self.assertRegex(str(e.exception), r'chicken')
        self.assertRegex(str(e.exception), r'egg')

    def test_steps_order(self):
        plugins = [_TestPlugin1(), _TestPlugin2(), _TestPlugin3()]
        pm = PluginManagerImpl(plugins)

        self.assertEqual(
            list(pm.get_operation_sequence('init')),
            [
                OperationStep(plugins[2].init, '_TestPlugin3.init', plugins[2], (), ('_TestPlugin1.init',)),
                OperationStep(plugins[0].init, '_TestPlugin1.init', plugins[0], (), ()),
                OperationStep(plugins[1].init, '_TestPlugin2.init', plugins[1], ('_TestPlugin1.init',), ()),
            ]
        )


if __name__ == '__main__':
    unittest.main()
