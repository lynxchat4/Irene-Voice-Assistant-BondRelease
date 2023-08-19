import unittest

import snapshottest  # type: ignore

from irene.constants.gender import FEMALE, MALE, NEUTER
from irene.constants.word_forms import WordCaseRU, FullKnownFormsRU, KnownFormsRU
from irene.utils.pronounce_numbers_ru import pronounce_sub_thousand

THING = FullKnownFormsRU(
    singular=KnownFormsRU("штуковина", "штуковины", "штуковине", "штуковину", "штуковиной", "штуковине"),
    plural=KnownFormsRU("штуковины", "штуковин", "штуковинам", "штуковины", "штуковинами", "штуковинах"),
    gender=FEMALE.code,
)

SUN = FullKnownFormsRU(
    singular=KnownFormsRU("солнце", "солнца", "солнцу", "солнце", "солнцем", "солнце"),
    plural=KnownFormsRU("солнца", "солнц", "солнцам", "солнца", "солнцами", "солнцах"),
    gender=NEUTER.code,
)

CAT_M = FullKnownFormsRU(
    singular=KnownFormsRU("кот", "кота", "коту", "кота", "котом", "коте"),
    plural=KnownFormsRU("коты", "котов", "котам", "котов", "котами", "котах"),
    gender=MALE.code,
    animated=True,
)

CAT_F = FullKnownFormsRU(
    singular=KnownFormsRU("кошка", "кошки", "кошке", "кошку", "кошкой", "кошке"),
    plural=KnownFormsRU("кошки", "кошек", "кошкам", "кошек", "кошками", "кошках"),
    gender=FEMALE.code,
    animated=True,
)


class PronounceNumbersSubThousandRuTest(snapshottest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = 100000

    def _test_for_word(self, word: FullKnownFormsRU):
        result = '\n'.join(
            case.format_check_phrase(' '.join(pronounce_sub_thousand(number, word, case)))
            for number in range(100)
            for case in WordCaseRU
        )

        self.assertMatchSnapshot(result)

    def test_thing_sub_100(self):
        self._test_for_word(THING)

    def test_sun_sub_100(self):
        self._test_for_word(SUN)

    def test_male_cat_sub_100(self):
        self._test_for_word(CAT_M)

    def test_female_cat_sub_100(self):
        self._test_for_word(CAT_F)


if __name__ == '__main__':
    unittest.main()
