import unittest

from irene.test_utuls.plugin_test_case import PluginTestCase


class DefaultGreetingsTest(PluginTestCase):
    plugin = '../plugin_greetings.py'

    def test_greeting(self):
        self.play_scenario("""
        > привет
        < И тебе привет!|Рада тебя видеть!
        """)


class ConfiguredGreetingsTest(PluginTestCase):
    plugin = '../plugin_greetings.py'
    configs = {
        'greetings': {
            'phrases': ['Привет, кожаный мешок!']
        }
    }

    def test_greeting(self):
        self.play_scenario("""
        > привет
        < Привет, кожаный мешок!
        """)


if __name__ == '__main__':
    unittest.main()
