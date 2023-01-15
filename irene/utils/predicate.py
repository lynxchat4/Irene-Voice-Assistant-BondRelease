from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Callable, Optional

T = TypeVar('T')

PredicateLike = Callable[[T], bool]
OptionalPredicateLike = Optional[PredicateLike]


class Predicate(ABC, Generic[T]):
    @abstractmethod
    def __call__(self, arg: T) -> bool:
        ...

    def __and__(self, other: OptionalPredicateLike) -> 'Predicate[T]':
        if other is None:
            return self

        return And(self, other)

    def __or__(self, other: OptionalPredicateLike) -> 'Predicate[T]':
        if other is None:
            return self

        return Or(self, other)

    def __invert__(self) -> 'Predicate[T]':
        return Not(self)

    @staticmethod
    def from_callable(cb: PredicateLike) -> 'Predicate[T]':
        if isinstance(cb, Predicate):
            return cb

        return CallablePredicate(cb)

    @staticmethod
    def true() -> 'Predicate[T]':
        return TruePredicate()

    @staticmethod
    def false() -> 'Predicate[T]':
        return FalsePredicate()


class TruePredicate(Predicate):
    def __call__(self, arg: T) -> bool:
        return True

    def __and__(self, other: OptionalPredicateLike) -> Predicate[T]:
        return self if other is None else Predicate.from_callable(other)

    def __or__(self, other: OptionalPredicateLike) -> Predicate[T]:
        return self


class FalsePredicate(Predicate):
    def __call__(self, arg: T) -> bool:
        return False

    def __and__(self, other: OptionalPredicateLike) -> Predicate[T]:
        return self

    def __or__(self, other: OptionalPredicateLike) -> Predicate[T]:
        return self if other is None else Predicate.from_callable(other)


class CallablePredicate(Predicate):
    def __init__(self, cb: PredicateLike):
        self._cb = cb

    def __call__(self, arg: T) -> bool:
        return self._cb(arg)


class And(Predicate):
    def __init__(self, a: PredicateLike, b: PredicateLike):
        self._a, self._b = a, b

    def __call__(self, arg: T) -> bool:
        return self._a(arg) and self._b(arg)


class Or(Predicate):
    def __init__(self, a: PredicateLike, b: PredicateLike):
        self._a, self._b = a, b

    def __call__(self, arg: T) -> bool:
        return self._a(arg) or self._b(arg)


class Not(Predicate):
    def __init__(self, x: PredicateLike):
        self._x = x

    def __call__(self, arg: T) -> bool:
        return not self._x(arg)

    def __invert__(self):
        return self._x
