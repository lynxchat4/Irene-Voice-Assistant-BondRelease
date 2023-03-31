import unittest

from irene.utils.all_num_to_text import all_num_to_text, load_language


class AllNumsToTextTest(unittest.TestCase):
    def setUp(self):
        load_language('ru-RU')

    def test_percent(self):
        self.assertEqual(
            all_num_to_text("Рынок -10%."),
            "Рынок минус десять процентов."
        )

    @unittest.skip("Не работает")
    def test_one_percent(self):
        # TODO: Исправить
        self.assertEqual(
            all_num_to_text("Рынок -1%."),
            "Рынок минус один процент."
        )

    def test(self):
        self.assertEqual(
            all_num_to_text(
                "Ба ва 120.1-120.8, Да -30.1, Ка 44.05, Га 225. Рынок -10%. Тест"),
            "Ба ва сто двадцать точка один тире сто двадцать точка восемь, Да минус тридцать точка один, "
            "Ка сорок четыре точка ноль пять, Га двести двадцать пять. Рынок минус десять процентов. Тест"
        )


if __name__ == '__main__':
    unittest.main()
