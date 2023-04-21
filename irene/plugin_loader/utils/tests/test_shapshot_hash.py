import hashlib
import unittest

from irene.plugin_loader.utils.snapshot_hash import snapshot_hash, make_stable_hash_fn


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

    def test_hash_stable(self):
        self.assertEqual(
            snapshot_hash({'foo': ['bar']}),
            37133252672926233695994809505992682454371366431544797706692903489691835070470
        )

        self.assertEqual(
            snapshot_hash({'foo': ['bar']}, make_stable_hash_fn(hashlib.md5)),
            59139101794391242901173294103234746387
        )


if __name__ == '__main__':
    unittest.main()
