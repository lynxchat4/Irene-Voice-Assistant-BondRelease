from abc import ABCMeta
from typing import Any, Mapping

from irene.utils.mapping_match import mapping_match
from irene.utils.predicate import Predicate

MetadataMapping = Mapping[str, Any]


class Metadata(metaclass=ABCMeta):
    """
    Базовый класс для объектов, имеющих дополнительные метаданные.
    """
    __slots__ = ()

    @property
    def meta(self) -> MetadataMapping:
        return {}


class MetaMatcher(Predicate[Metadata]):
    """
    Предикат, сравнивающий метаданные полученного объекта с шаблоном.
    """
    __slots__ = '_query'

    def __init__(self, query: MetadataMapping):
        self._query = query

    def __call__(self, arg: Metadata) -> bool:
        return mapping_match(arg.meta, self._query)
