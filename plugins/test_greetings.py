import unittest

import plugin_greetings
from test_utuls.dialogtestcase import PluginDialogTestCase


class GreetingsPluginTest(PluginDialogTestCase):
    plugin = plugin_greetings

    def test_greeting(self):
        self.play_scenario("""
        > привет
        < И тебе привет!|Рада тебя видеть!
        """)


if __name__ == '__main__':
    unittest.main()
