import unittest

from irene import construct_context, VAContext, VAApiExt, VAContextSource
from irene.brain.command_tree import VACommandTree
from irene.brain.contexts import CommandTreeContext
from irene.plugin_loader.abc import PluginManager
from irene.plugin_loader.run_operation import call_all_as_wrappers
from irene.test_utuls import PluginTestCase


class _CustomException(Exception):
    pass


def _construct_root_context(pm: PluginManager) -> VAContext:
    tree: VACommandTree[VAContext] = VACommandTree()

    def _reply(text: str) -> VAContextSource:
        def _fn(va: VAApiExt, rest: str):
            va.say(text)

        return _fn

    def _break(_va: VAApiExt, _rest: str):
        raise _CustomException()

    tree.add_commands(
        {
            "привет": _reply("И тебе привет"),
            "пока": _reply("И тебе пока"),
            "сломайся": _break
        },
        construct_context
    )

    ctx = CommandTreeContext(tree)

    return call_all_as_wrappers(
        pm.get_operation_sequence('create_root_context'),
        ctx,
        pm
    )


class _BaseAliasesTest(PluginTestCase):
    plugin = '../plugin_command_aliases.py'

    def using_context_with_aliases(self):
        self.using_context(_construct_root_context(self.pm))


class AliasesPluginDefaultConfigTest(_BaseAliasesTest):
    def test_default_config(self):
        self.using_context_with_aliases()

        self.play_scenario("""
            > здравствуй
            < И тебе привет
        """)
        self.play_scenario("""
            > здорова
            < И тебе привет
        """)

    def test_aliasless_commands(self):
        self.using_context_with_aliases()

        self.play_scenario("""
            > привет
            < И тебе привет
        """)
        self.play_scenario("""
            > пока
            < И тебе пока
        """)


class AliasesPluginRecursiveConfigTest(_BaseAliasesTest):
    configs = {
        'command_aliases': {
            'command_aliases': [
                {
                    'command': "привет",
                    'aliases': ["здорова"]
                },
                {
                    'command': "здорова",
                    'aliases': ["хаюшки"]
                },
                {
                    'command': "сломайся",
                    'aliases': ["зависни"]
                },
                {
                    'command': "зависни",
                    'aliases': ["сломайся"]
                }
            ]
        }
    }

    def test_recursive_config(self):
        self.using_context_with_aliases()

        self.play_scenario("""
            > хаюшки
            < И тебе привет
        """)

    def test_infinite_recursion(self):
        self.using_context_with_aliases()

        with self.assertRaises(_CustomException):
            self.say("сломайся")


class AliasesPluginSwapConfigTest(_BaseAliasesTest):
    configs = {
        'command_aliases': {
            'command_aliases': [
                {
                    'command': "привет",
                    'aliases': "пока",
                    'forbid_recursion': True,
                },
                {
                    'command': "пока",
                    'aliases': "привет",
                    'forbid_recursion': True,
                },
            ]
        }
    }

    def test_swap_config(self):
        self.using_context_with_aliases()

        self.play_scenario("""
            > пока
            < И тебе привет
        """)
        self.play_scenario("""
            > привет
            < И тебе пока
        """)


class AliasesPluginDuplicateConfigTest(_BaseAliasesTest):
    configs = {
        'command_aliases': {
            'command_aliases': [
                {
                    'command': "пока",
                    'aliases': "пакетик",
                    'forbid_recursion': True,
                },
                {
                    'command': "пока",
                    'aliases': "пакетик",
                },
            ]
        }
    }

    def test_duplicate_config(self):
        self.using_context_with_aliases()

        self.play_scenario("""
            > пакетик
            < И тебе пока
        """)


if __name__ == '__main__':
    unittest.main()
