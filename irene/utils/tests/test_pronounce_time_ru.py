import unittest
from datetime import time

import snapshottest  # type: ignore

from irene.utils.pronounce_time_ru import pronounce_time_ru

_TEST_MINUTES = (0, 1, 5, 10, 14, 15, 16, 20, 25, 29, 30, 31, 40, 42, 44, 45, 46, 50, 55, 59)


class MyTestCase(snapshottest.TestCase):
    def _test_with_settings(self, **kwargs):
        result = '\n'.join(
            f"{t.hour:02d}:{t.minute:02d} -> {' '.join(pronounce_time_ru(t, **kwargs))}"
            for t in (time(hour=h, minute=m) for h in range(24) for m in _TEST_MINUTES)
        )

        self.assertMatchSnapshot(result)

    def test_with_default_settings(self):
        self._test_with_settings()


if __name__ == '__main__':
    unittest.main()
