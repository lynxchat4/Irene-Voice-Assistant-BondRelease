import unittest
from unittest.mock import Mock

from irene.output_pool import OutputPoolImpl
from irene.va_abc import TextOutputChannel, AudioOutputChannel, OutputChannel, OutputChannelNotFoundError


class _CustomOutputChannel(OutputChannel):
    pass


class OutputPoolTest(unittest.TestCase):
    text_out = Mock(spec=TextOutputChannel)
    audio_out = Mock(spec=AudioOutputChannel)

    def test_get_right_type(self):
        pool = OutputPoolImpl([self.text_out, self.audio_out])

        self.assertEqual(
            pool.get_channels(TextOutputChannel),
            [self.text_out]
        )
        self.assertEqual(
            pool.get_channels(AudioOutputChannel),
            [self.audio_out]
        )

    def test_return_multiple(self):
        pool = OutputPoolImpl([self.text_out, self.audio_out])

        self.assertEqual(
            pool.get_channels(OutputChannel),
            [self.text_out, self.audio_out]
        )

    def test_raise_when_not_found(self):
        pool = OutputPoolImpl([self.text_out, self.audio_out])

        with self.assertRaises(OutputChannelNotFoundError):
            pool.get_channels(_CustomOutputChannel)


if __name__ == '__main__':
    unittest.main()
