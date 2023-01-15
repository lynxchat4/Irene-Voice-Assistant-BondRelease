import unittest

from irene.utils.mapping_match import mapping_match


class MappingMatchTest(unittest.TestCase):
    def test_match(self):
        self.assertTrue(
            mapping_match(
                {
                    'foo': 'bar',
                    'baz': 'buz',
                    'zoo': 'boo',
                },
                {
                    'foo': 'bar',
                    'baz': 'buz',
                }
            )
        )

    def test_no_match(self):
        self.assertFalse(
            mapping_match(
                {
                    'foo': 'bar',
                    'baz': 'buz',
                    'zoo': 'boo',
                },
                {
                    'foo': 'bar',
                    'baz': 'boo',
                }
            )
        )

    def test_no_match_missing_key(self):
        self.assertFalse(
            mapping_match(
                {
                    'foo': 'bar',
                    'baz': 'buz',
                    'zoo': 'boo',
                },
                {
                    'boo': 'foo',
                }
            )
        )


if __name__ == '__main__':
    unittest.main()
