from typing import NamedTuple, Optional

from irene.constants.gender import FEMALE, MALE, NEUTER, GenderCode
from irene.constants.word_forms import KnownFormsRU, FullKnownFormsRU, WordCaseRU


class NumeralFormsRU(NamedTuple):
    number: int
    female: KnownFormsRU
    male: Optional[KnownFormsRU] = None
    neuter: Optional[KnownFormsRU] = None
    female_animated: Optional[KnownFormsRU] = None
    male_animated: Optional[KnownFormsRU] = None
    neuter_animated: Optional[KnownFormsRU] = None

    def get_form(self, gender: GenderCode, case: WordCaseRU, animated: bool) -> str:
        # TODO: Добавить поддержку множественных существительных e.g. "одни штаны"
        assert gender in {MALE.code, FEMALE.code, NEUTER.code}

        form: Optional[KnownFormsRU] = None

        if animated:
            form = getattr(self, f"{gender}_animated")

        if form is None:
            form = getattr(self, gender)

        final_form: KnownFormsRU = self.female

        if form is not None:
            final_form = form

        return final_form.get_for_case(case)


NUMBERS = (
    NumeralFormsRU(
        number=0,
        female=KnownFormsRU("ноль", "нуля", "нулю", "ноль", "нулём", "нуле"),
        male=KnownFormsRU("ноль", "нуля", "нулю", "ноль", "нулём", "нуле"),
        neuter=KnownFormsRU("ноль", "нуля", "нулю", "ноль", "нулём", "нуле"),
    ),
    NumeralFormsRU(
        number=1,
        female=KnownFormsRU("одна", "одной", "одной", "одну", "одной", "одной"),
        male=KnownFormsRU("один", "одного", "одному", "один", "одним", "одном"),
        male_animated=KnownFormsRU("один", "одного", "одному", "одного", "одним", "одном"),
        neuter=KnownFormsRU("одно", "одного", "одному", "одно", "одним", "одном"),
    ),
    NumeralFormsRU(
        number=2,
        female=KnownFormsRU("две", "двух", "двум", "две", "двумя", "двух"),
        male=KnownFormsRU("два", "двух", "двум", "два", "двумя", "двух"),
        male_animated=KnownFormsRU("два", "двух", "двум", "двух", "двумя", "двух"),
        female_animated=KnownFormsRU("две", "двух", "двум", "двух", "двумя", "двух"),
        neuter=KnownFormsRU("два", "двух", "двум", "два", "двумя", "двух"),
    ),
    NumeralFormsRU(
        number=3,
        female=KnownFormsRU("три", "трёх", "трём", "три", "тремя", "трёх"),
        male_animated=KnownFormsRU("три", "трёх", "трём", "трёх", "тремя", "трёх"),
        female_animated=KnownFormsRU("три", "трёх", "трём", "трёх", "тремя", "трёх"),
    ),
    NumeralFormsRU(
        number=4,
        female=KnownFormsRU("четыре", "четырёх", "четырём", "четыре", "четырьмя", "четырёх"),
        male_animated=KnownFormsRU("четыре", "четырёх", "четырём", "четырёх", "четырьмя", "четырёх"),
        female_animated=KnownFormsRU("четыре", "четырёх", "четырём", "четырёх", "четырьмя", "четырёх"),
    ),
    NumeralFormsRU(
        number=5,
        female=KnownFormsRU("пять", "пяти", "пяти", "пять", "пятью", "пяти"),
    ),
    NumeralFormsRU(
        number=6,
        female=KnownFormsRU("шесть", "шести", "шести", "шесть", "шестью", "шести"),
    ),
    NumeralFormsRU(
        number=7,
        female=KnownFormsRU("семь", "семи", "семи", "семь", "семью", "семи"),
    ),
    NumeralFormsRU(
        number=8,
        female=KnownFormsRU("восемь", "восьми", "восьми", "восемь", "восемью", "восьми"),
    ),
    NumeralFormsRU(
        number=9,
        female=KnownFormsRU("девять", "девяти", "девяти", "девять", "девятью", "девяти"),
    ),
    NumeralFormsRU(
        number=10,
        female=KnownFormsRU("десять", "десяти", "десяти", "десять", "десятью", "десяти"),
    ),
    NumeralFormsRU(
        number=11,
        female=KnownFormsRU("одиннадцать", "одиннадцати", "одиннадцати", "одиннадцать", "одиннадцатью", "одиннадцати"),
    ),
    NumeralFormsRU(
        number=12,
        female=KnownFormsRU("двенадцать", "двенадцати", "двенадцати", "двенадцать", "двенадцатью", "двенадцати"),
    ),
    NumeralFormsRU(
        number=13,
        female=KnownFormsRU("тринадцать", "тринадцати", "тринадцати", "тринадцать", "тринадцатью", "тринадцати"),
    ),
    NumeralFormsRU(
        number=14,
        female=KnownFormsRU("четырнадцать", "четырнадцати", "четырнадцати", "четырнадцать", "четырнадцатью",
                            "четырнадцати"),
    ),
    NumeralFormsRU(
        number=15,
        female=KnownFormsRU("пятнадцать", "пятнадцати", "пятнадцати", "пятнадцать", "пятнадцатью", "пятнадцати"),
    ),
    NumeralFormsRU(
        number=16,
        female=KnownFormsRU("шестнадцать", "шестнадцати", "шестнадцати", "шестнадцать", "шестнадцатью", "шестнадцати"),
    ),
    NumeralFormsRU(
        number=17,
        female=KnownFormsRU("семнадцать", "семнадцати", "семнадцати", "семнадцать", "семнадцатью", "семнадцати"),
    ),
    NumeralFormsRU(
        number=18,
        female=KnownFormsRU("восемнадцать", "восемнадцати", "восемнадцати", "восемнадцать", "восемнадцатью",
                            "восемнадцати"),
    ),
    NumeralFormsRU(
        number=19,
        female=KnownFormsRU("девятнадцать", "девятнадцати", "девятнадцати", "девятнадцать", "девятнадцатью",
                            "девятнадцати"),
    ),
)

DECADES = (
    None,
    None,
    KnownFormsRU("двадцать", "двадцати", "двадцати", "двадцать", "двадцатью", "двадцати"),
    KnownFormsRU("тридцать", "тридцати", "тридцати", "тридцать", "тридцатью", "тридцати"),
    KnownFormsRU("сорок", "сорока", "сорока", "сорок", "сорока", "сорока"),
    KnownFormsRU("пятьдесят", "пятидесяти", "пятидесяти", "пятьдесят", "пятьюдесятью", "пятидесяти"),
    KnownFormsRU("шестьдесят", "шестидесяти", "шестидесяти", "шестьдесят", "шестьюдесятью", "шестидесяти"),
    KnownFormsRU("семьдесят", "семидесяти", "семидесяти", "семьдесят", "семьюдесятью", "семидесяти"),
    KnownFormsRU("восемьдесят", "восьмидесяти", "восьмидесяти", "восемьдесят", "восьмьюдесятью", "восьмидесяти"),
    KnownFormsRU("девяносто", "девяноста", "девяноста", "девяносто", "девяноста", "девяноста"),
)

HUNDREDS: tuple[Optional[KnownFormsRU], ...] = (
    None,
    KnownFormsRU("сто", "ста", "ста", "сто", "ста", "ста"),
    KnownFormsRU("двести", "двухсот", "двум стам", "двести", "двумя стами", "двух стах"),
    KnownFormsRU("триста", "трёхсот", "трём стам", "триста", "тремя стами", "трёх стах"),
    KnownFormsRU("четыреста", "четырёхсот", "четырём стам", "четыреста", "четырьмя стами", "четырёх стах"),
    KnownFormsRU("пятьсот", "пятисот", "пятистам", "пятьсот", "пяти стами", "пяти стах"),
    KnownFormsRU("шестьсот", "шестисот", "шестистам", "шестьсот", "шестистами", "шестистах"),
    KnownFormsRU("семьсот", "семисот", "семистам", "семьсот", "семью стами", "семистах"),
    KnownFormsRU("восемьсот", "восьми ста", "восьмистам", "восемьсот", "восьмью стами", "восьми ста"),
    KnownFormsRU("девятьсот", "девяти ста", "девятистам", "девятьсот", "девяти стами", "девяти ста"),
)

THOUSAND = FullKnownFormsRU(
    singular=KnownFormsRU("тысяча", "тысячи", "тысяче", "тысячу", "тысячей", "тысяче"),
    plural=KnownFormsRU("тысячи", "тысяч", "тысячам", "тысячи", "тысячами", "тысячах"),
    gender=FEMALE.code,
)

MILLION = FullKnownFormsRU(
    singular=KnownFormsRU("миллион", "миллиона", "миллиону", "миллион", "миллионом", "миллионе"),
    plural=KnownFormsRU("миллионы", "миллионов", "миллионам", "миллионы", "миллионами", "миллионах"),
    gender=MALE.code,
)

MAGNITUDES: tuple[tuple[int, FullKnownFormsRU], ...] = (
    (1_000_000, MILLION),
    (1_000, THOUSAND)
)
