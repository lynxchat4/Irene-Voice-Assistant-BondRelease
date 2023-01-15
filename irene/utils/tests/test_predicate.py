import unittest

from irene.utils.predicate import Predicate

gt_1: Predicate[float] = Predicate.from_callable(lambda it: it > 1)
gt_5: Predicate[float] = Predicate.from_callable(lambda it: it > 5)
lt_9: Predicate[float] = Predicate.from_callable(lambda it: it < 9)
lt_0: Predicate[float] = Predicate.from_callable(lambda it: it < 0)


class PredicateTest(unittest.TestCase):
    def test_simple_call(self):
        self.assertTrue(gt_1(2))
        self.assertFalse(gt_5(2))

    def test_inverse(self):
        self.assertFalse((~gt_1)(2))
        self.assertTrue((~gt_5)(2))

    def test_double_inverse(self):
        ngt_1 = ~gt_1
        self.assertIsNot(ngt_1, gt_1)
        self.assertIs(
            ~ngt_1,
            gt_1
        )

    def test_constant(self):
        self.assertTrue(Predicate.true()(1))
        self.assertFalse(Predicate.false()(1))

    def test_constants_composition(self):
        true, false = Predicate.true(), Predicate.false()

        self.assertIs(true & gt_1, gt_1)
        self.assertIs(true | gt_1, true)
        self.assertIs(false & gt_1, false)
        self.assertIs(false | gt_1, gt_1)

    def test_composition_and(self):
        pr = gt_1 & lt_9

        self.assertFalse(pr(0))
        self.assertFalse(pr(10))
        self.assertTrue(pr(5))

    def test_composition_or(self):
        pr = lt_0 | gt_5

        self.assertTrue(pr(-1))
        self.assertTrue(pr(10))
        self.assertFalse(pr(4))


if __name__ == '__main__':
    unittest.main()
