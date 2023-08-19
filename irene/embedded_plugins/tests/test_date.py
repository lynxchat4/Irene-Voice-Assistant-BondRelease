import unittest
from datetime import datetime, timezone

from time_machine import travel

from irene.test_utuls import PluginTestCase

LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo


class DateSkillTest(PluginTestCase):
    plugin = '../plugin_date.py'

    @travel(datetime(2022, 11, 10, 18, 10, tzinfo=LOCAL_TIMEZONE))
    def test_date(self):
        self.play_scenario("""
        > дата
        < сегодня четверг, десятое ноября
        """)


if __name__ == '__main__':
    unittest.main()
