import unittest

from irene.test_utuls.dialogtestcase import PluginDialogTestCase


class GreetingsPluginTest(PluginDialogTestCase):
    plugin = 'plugins/plugin_greetings.py'

    def test_greeting(self):
        self.play_scenario("""
        > привет
        < И тебе привет!|Рада тебя видеть!
        """)


if __name__ == '__main__':
    unittest.main()
