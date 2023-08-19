from random import random
from typing import Union

ProbabilisticFlag = Union[bool, float]


def get_probabilistic_flag(value: ProbabilisticFlag) -> bool:
    if isinstance(value, bool):
        return value

    return random() < value
