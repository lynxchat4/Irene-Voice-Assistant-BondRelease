from typing import Collection

from irene.constants.numerals_ru import HUNDREDS, DECADES, NUMBERS, MAGNITUDES
from irene.constants.word_forms import FullKnownFormsRU, WordCaseRU


def pronounce_sub_thousand(num: int, known: FullKnownFormsRU, case: WordCaseRU) -> Collection[str]:
    assert num >= 0
    assert num < 1000

    num_initial = num
    result = []

    if (hundreds_forms := HUNDREDS[num // 100]) is not None:
        num = num % 100

        result.append(hundreds_forms.get_for_case(case if num == 0 else WordCaseRU.NOMINATIVE))

    if (decades_forms := DECADES[num // 10]) is not None:
        num = num % 10

        result.append(decades_forms.get_for_case(WordCaseRU.NOMINATIVE if num == 1 else case))

    if num != 0 or len(result) == 0:
        result.append(NUMBERS[num].get_form(known.gender, case, known.animated))

    # В русском языке числительные два, три, четыре в именительном и неодушевлённом
    # винительном падежах требуют родительного падежа единственного числа (точнее — паукальной счётной формы)
    if (2 <= num <= 4) and (case is WordCaseRU.NOMINATIVE or (case is WordCaseRU.ACCUSATIVE and not known.animated)):
        result.append(known.singular.get_for_case(WordCaseRU.GENITIVE))
    elif num == 1:
        result.append(known.singular.get_for_case(case))
    elif num_initial == 0 or case is WordCaseRU.NOMINATIVE or case is WordCaseRU.ACCUSATIVE:
        result.append(known.plural.get_for_case(WordCaseRU.GENITIVE))
    else:
        result.append(known.plural.get_for_case(case))

    return result


MAX_PRONOUNCEABLE_NUMBER = 999 + sum(map(lambda it: it[0] * 999, MAGNITUDES))


def pronounce_integer(num: int, known: FullKnownFormsRU, case: WordCaseRU) -> Collection[str]:
    if abs(num) > MAX_PRONOUNCEABLE_NUMBER:
        raise ValueError(f"Не возможно произнести числа больше {MAX_PRONOUNCEABLE_NUMBER}")

    num_initial = num
    result = []

    if num < 0:
        result.append("минус")
        num = -num

    for (magnitude, word) in MAGNITUDES:
        if num >= magnitude:
            n = num // magnitude
            num = num % magnitude

            result.extend(pronounce_sub_thousand(n, word, case))

    if num_initial != 0 and num == 0:
        result.append(known.plural.get_for_case(WordCaseRU.GENITIVE))
    else:
        result.extend(pronounce_sub_thousand(num, known, case))

    return result
