import unittest

from irene.brain.command_tree import VACommandTree, ConflictingCommandsException, AmbiguousCommandException, \
    NoCommandMatchesException


def _constructor(src: str) -> str:
    return f'cmd_{src}'


class VACommandTreeTest(unittest.TestCase):
    def setUp(self):
        self.tree = VACommandTree()
        self.tree.add_commands(
            {
                "дата": 'date',
                "выключи": {
                    "плеер": 'disable_player',
                    "звук": 'mute',
                },
                "включи": {
                    "звук": 'un-mute'
                },
                "останови|стоп": 'stop',
                "останови коня": 'stop_the_horse',
            },
            _constructor
        )

    def assert_result(self, input_text: str, action_name: str, additional_text: str = ''):
        self.assertEqual(
            self.tree.get_command(input_text),
            (_constructor(action_name), additional_text)
        )

    def test_simple_key(self):
        self.assert_result("дата", 'date')

    def test_nested_key(self):
        self.assert_result("выключи звук", 'mute')
        self.assert_result("выключи плеер", 'disable_player')

    def test_varying_key(self):
        self.assert_result("останови", 'stop')
        self.assert_result("стоп", 'stop')

    def test_long_key(self):
        self.assert_result("останови коня", 'stop_the_horse')

    def test_additional_text(self):
        self.assert_result("выключи звук немедленно", 'mute', "немедленно")

    def test_additional_text_multiple_words(self):
        self.assert_result("выключи звук немедленно пожалуйста",
                           'mute', "немедленно пожалуйста")

    def test_add_conflicting_rules(self):
        with self.assertRaises(ConflictingCommandsException) as e:
            self.tree.add_commands(
                {
                    "останови": {
                        "коня|лошадь": 'stop_the_horse_dup',
                    }
                },
                _constructor
            )
        self.assertRegex(
            str(e.exception),
            r'"останови коня"'
        )

    def test_ambiguous_command(self):
        with self.assertRaises(AmbiguousCommandException) as e:
            self.tree.get_command("включи выключи звук")

        self.assertRegex(
            str(e.exception),
            r'"включи выключи звук"'
        )

    def test_unknown_command(self):
        with self.assertRaises(NoCommandMatchesException) as e:
            self.tree.get_command("включи свет")

        self.assertRegex(
            str(e.exception),
            r'"включи свет"'
        )

    def test_add_intersecting_command(self):
        self.tree.add_commands(
            {
                "выключи": {
                    "свет": 'light_off'
                }
            },
            _constructor
        )

        self.assert_result("выключи свет", 'light_off')
        self.assert_result("выключи звук", 'mute')


if __name__ == '__main__':
    unittest.main()
