import unittest
from datetime import datetime, timezone

from time_machine import travel

from irene.test_utuls import PluginTestCase

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


class DefaultDatetimeTest(PluginTestCase):
    plugin = '../plugin_datetime.py'

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

    @travel(datetime(2022, 11, 10, 18, 10, tzinfo=LOCAL_TIMEZONE))
    def test_date(self):
        self.play_scenario("""
        > дата
        < сегодня четверг, десятое ноября
        """)


class NoUnitsTimeTest(PluginTestCase):
    plugin = '../plugin_datetime.py'

    configs = {
        'datetime': {
            'skipUnits': True
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
    plugin = '../plugin_datetime.py'

    configs = {
        'datetime': {
            'unitsSeparator': " и "
        }
    }

    @travel(datetime(2022, 11, 10, 18, 10, tzinfo=LOCAL_TIMEZONE))
    def test_time(self):
        self.play_scenario("""
        > время
        < Сейчас восемнадцать часов и десять минут
        """)

    @travel(datetime(2022, 11, 10, 18, 0, tzinfo=LOCAL_TIMEZONE))
    def test_time_zero_minutes(self):
        self.play_scenario("""
        > время
        < Сейчас ровно восемнадцать часов
        """)


class ExplicitMinutesTimeTest(PluginTestCase):
    plugin = '../plugin_datetime.py'

    configs = {
        'datetime': {
            'skipMinutesWhenZero': False
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
    plugin = '../plugin_datetime.py'

    configs = {
        'datetime': {
            'sayNoon': True
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
