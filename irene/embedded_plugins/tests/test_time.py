import unittest
from datetime import datetime, timezone

from time_machine import travel

from irene.test_utuls import PluginTestCase

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


class DigitalTimeTest(PluginTestCase):
    plugin = '../plugin_time.py'

    configs = {
        'skill_time': {
            'midday_enabled': False,
            'midnight_enabled': False,
            'exactly_before': True,
            'pronounce_exactly': True,
            'digital_format': True,
            'pronounce_hour_units': True,
            'digital_pronounce_minute_units': True,
            'digital_format_separator': None,
            'digital_skip_minutes_when_zero': True,
        }
    }

    @travel(datetime(2022, 11, 10, 18, 10, tzinfo=LOCAL_TIMEZONE))
    def test_time(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать часов десять минут
        """)

    @travel(datetime(2022, 11, 10, 18, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_zero_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас ровно восемнадцать часов
        """)

    @travel(datetime(2022, 11, 10, 0, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midnight(self):
        self.play_scenario("""
        > время
        < Сейчас ровно ноль часов
        """)

    @travel(datetime(2022, 11, 10, 12, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midday(self):
        self.play_scenario("""
        > время
        < Сейчас ровно двенадцать часов
        """)


class NoUnitsTimeTest(PluginTestCase):
    plugin = '../plugin_time.py'

    configs = {
        'skill_time': {
            'midday_enabled': False,
            'midnight_enabled': False,
            'exactly_before': True,
            'pronounce_exactly': True,
            'digital_format': True,
            'pronounce_hour_units': False,
            'digital_pronounce_minute_units': False,
            'digital_format_separator': None,
            'digital_skip_minutes_when_zero': True,
        }
    }

    @travel(datetime(2022, 11, 10, 18, 10, tzinfo=LOCAL_TIMEZONE))
    def test_time(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать десять
        """)

    @travel(datetime(2022, 11, 10, 18, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_zero_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас ровно восемнадцать
        """)

    @travel(datetime(2022, 11, 10, 0, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midnight(self):
        self.play_scenario("""
        > время
        < Сейчас ровно ноль
        """)

    @travel(datetime(2022, 11, 10, 12, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midday(self):
        self.play_scenario("""
        > время
        < Сейчас ровно двенадцать
        """)


class CustomSeparatorTimeTest(PluginTestCase):
    plugin = '../plugin_time.py'

    configs = {
        'skill_time': {
            'midday_enabled': True,
            'midnight_enabled': True,
            'exactly_before': True,
            'pronounce_exactly': True,
            'digital_format': True,
            'pronounce_hour_units': True,
            'digital_pronounce_minute_units': True,
            'digital_format_separator': "да",
            'digital_skip_minutes_when_zero': True,
        }
    }

    @travel(datetime(2022, 11, 10, 18, 10, tzinfo=LOCAL_TIMEZONE))
    def test_time(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать часов да десять минут
        """)

    @travel(datetime(2022, 11, 10, 18, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_zero_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас ровно восемнадцать часов
        """)


class MinimalDigitalTimeTest(PluginTestCase):
    plugin = '../plugin_time.py'

    configs = {
        'skill_time': {
            'midday_enabled': False,
            'midnight_enabled': False,
            'exactly_before': True,
            'pronounce_exactly': False,
            'digital_format': True,
            'pronounce_hour_units': False,
            'digital_pronounce_minute_units': False,
            'digital_format_separator': None,
            'digital_skip_minutes_when_zero': False,
        }
    }

    @travel(datetime(2022, 11, 10, 18, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_zero_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать ноль ноль
        """)

    @travel(datetime(2022, 11, 10, 18, 2, tzinfo=LOCAL_TIMEZONE))
    def test_time_two_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать ноль две
        """)

    @travel(datetime(2022, 11, 10, 18, 32, tzinfo=LOCAL_TIMEZONE))
    def test_time_32_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать тридцать две
        """)


class ExplicitMinutesTimeTest(PluginTestCase):
    plugin = '../plugin_time.py'

    configs = {
        'skill_time': {
            'midday_enabled': False,
            'midnight_enabled': False,
            'exactly_before': True,
            'pronounce_exactly': False,
            'digital_format': True,
            'pronounce_hour_units': True,
            'digital_pronounce_minute_units': True,
            'digital_format_separator': None,
            'digital_skip_minutes_when_zero': False,
        }
    }

    @travel(datetime(2022, 11, 10, 18, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_zero_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать часов ноль минут
        """)

    @travel(datetime(2022, 11, 10, 0, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midnight(self):
        self.play_scenario("""
        > время
        < Сейчас ноль часов ноль минут
        """)

    @travel(datetime(2022, 11, 10, 12, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midday(self):
        self.play_scenario("""
        > время
        < Сейчас двенадцать часов ноль минут
        """)


class NoonTimeTest(PluginTestCase):
    plugin = '../plugin_time.py'

    configs = {
        'skill_time': {
            'midday_enabled': True,
            'midnight_enabled': True,
            'exactly_before': True,
            'pronounce_exactly': True,
            'digital_format': True,
            'pronounce_hour_units': True,
            'digital_skip_minutes_when_zero': True,
        }
    }

    @travel(datetime(2022, 11, 10, 18, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_zero_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас ровно восемнадцать часов
        """)

    @travel(datetime(2022, 11, 10, 0, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midnight(self):
        self.play_scenario("""
        > время
        < Сейчас ровно полночь
        """)

    @travel(datetime(2022, 11, 10, 12, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_midday(self):
        self.play_scenario("""
        > время
        < Сейчас ровно полдень
        """)


if __name__ == '__main__':
    unittest.main()
