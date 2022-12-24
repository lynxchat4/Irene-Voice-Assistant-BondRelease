import unittest
from typing import Optional

from irene.face.abc import Muteable
from irene.face.mute_group import MuteGroupImpl


class TestMuteable(Muteable):
    def __init__(self):
        self.muted: Optional[bool] = None

    def mute(self):
        self.muted = True

    def unmute(self):
        self.muted = False


class MuteGroupTest(unittest.TestCase):
    def test_raise_on_extra_unmutes(self):
        mg = MuteGroupImpl()

        with self.assertRaises(AssertionError):
            mg.unmute()

    def test_raise_on_extra_unmutes_1(self):
        mg = MuteGroupImpl()

        mg.mute()
        mg.unmute()

        with self.assertRaises(AssertionError):
            mg.unmute()

    def test_mute_one_muteable(self):
        m1 = TestMuteable()
        mg = MuteGroupImpl()
        mg.add_item(m1)

        self.assertIs(m1.muted, None)

        with mg.muted():
            self.assertIs(m1.muted, True)

        self.assertIs(m1.muted, False)

    def test_raise_on_extra_removals(self):
        m = TestMuteable()
        mg = MuteGroupImpl()
        rm = mg.add_item(m)

        rm()

        with self.assertRaises(AssertionError):
            rm()

    def test_mute_multiple(self):
        ms = [TestMuteable() for _ in range(10)]
        mg = MuteGroupImpl()

        for m in ms: mg.add_item(m)

        with mg.muted():
            self.assertTrue(all(it.muted for it in ms))

        self.assertTrue(all(not it.muted for it in ms))

    def test_add_while_muted(self):
        m = TestMuteable()
        mg = MuteGroupImpl()

        with mg.muted():
            mg.add_item(m)

            self.assertIs(m.muted, True)

        self.assertIs(m.muted, False)

    def test_remove_item_before_mute(self):
        m = TestMuteable()
        mg = MuteGroupImpl()
        rm = mg.add_item(m)

        rm()

        with mg.muted():
            self.assertIs(m.muted, None)

    def test_remove_while_muted(self):
        m = TestMuteable()
        mg = MuteGroupImpl()
        rm = mg.add_item(m)

        with mg.muted():
            rm()

            self.assertIs(m.muted, False)

        self.assertIs(m.muted, False)

    def test_remove_after_unmute(self):
        m = TestMuteable()
        mg = MuteGroupImpl()
        rm = mg.add_item(m)

        with mg.muted():
            ...

        rm()

        self.assertIs(m.muted, False)

        with mg.muted():
            self.assertIs(m.muted, False)


if __name__ == '__main__':
    unittest.main()
