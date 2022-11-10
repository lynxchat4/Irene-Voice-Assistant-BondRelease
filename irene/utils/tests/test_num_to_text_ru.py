import unittest

from irene.utils.num_to_text_ru import num2text, decimal2text


class NumToTextTest(unittest.TestCase):
    def test(self):
        self.assertEqual(
            num2text(0, main_units=((u'штука', u'штуки', u'штук'), 'f')),
            "ноль штук"
        )
        self.assertEqual(
            num2text(1, main_units=((u'штука', u'штуки', u'штук'), 'f')),
            "одна штука"
        )
        self.assertEqual(
            num2text(2, main_units=((u'штука', u'штуки', u'штук'), 'f')),
            "две штуки"
        )
        self.assertEqual(
            num2text(10, main_units=((u'штука', u'штуки', u'штук'), 'f')),
            "десять штук"
        )
        self.assertEqual(
            num2text(15, main_units=((u'штука', u'штуки', u'штук'), 'f')),
            "пятнадцать штук"
        )
        self.assertEqual(
            num2text(2345, main_units=((u'штука', u'штуки', u'штук'), 'f')),
            "две тысячи триста сорок пять штук"
        )
        self.assertEqual(
            num2text(-1, main_units=((u'штука', u'штуки', u'штук'), 'f')),
            "минус одна штука"
        )

    def test_empty_words(self):
        self.assertEqual(
            num2text(1, main_units=(('', '', ''), 'f')),
            "одна"
        )


class DecimalToTextTest(unittest.TestCase):
    def test(self):
        self.assertEqual(
            decimal2text(
                1.1,
                int_units=((u'штука', u'штуки', u'штук'), 'f'),
                exp_units=((u'кусок', u'куска', u'кусков'), 'm')
            ),
            "одна штука десять кусков"
        )


if __name__ == '__main__':
    unittest.main()
