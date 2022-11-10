import unittest

from irene.plugin_loader.utils.snapshot_hash import snapshot_hash


class SnapshotHashTest(unittest.TestCase):
    def test_hash_dict(self):
        self.assertEqual(
            snapshot_hash({'foo': {'bar': 42}}),
            snapshot_hash({'foo': {'bar': 42}}),
        )

    def test_hash_list(self):
        self.assertEqual(
            snapshot_hash([[42, ], 'foo']),
            snapshot_hash([[42, ], 'foo']),
        )

    def test_hash_difference(self):
        self.assertNotEqual(
            snapshot_hash({'foo': [{}, {'bar': 'baz'}]}),
            snapshot_hash({'foo': [{}, {'bar': 'buz'}]}),
        )


if __name__ == '__main__':
    unittest.main()
