import sys
import unittest
from pathlib import Path

from irene.plugin_loader.file_patterns import substitute_pattern


class FilePatternSubstitutionTest(unittest.TestCase):
    def test_default_simple_variables_substitution(self):
        res = set(substitute_pattern('{user_home}/foo/bar'))

        self.assertEqual(
            res,
            {f'{Path.home()}/foo/bar'}
        )

    def test_default_varying_variable_substitution(self):
        res = set(substitute_pattern('{python_path}/foo_bar_*'))

        self.assertEqual(
            res,
            {f'{p}/foo_bar_*' for p in sys.path}
        )

    def test_custom_variables_substitution(self):
        res = set(
            substitute_pattern(
                '/{v1}/{v2}/{v3}',
                override_vars=dict(v1=['var', 'opt'], v2=['lib', 'lib64'], v3='buz')
            )
        )

        self.assertEqual(
            res,
            {'/var/lib/buz', '/var/lib64/buz', '/opt/lib/buz', '/opt/lib64/buz'}
        )

    def test_unknown_variable(self):
        with self.assertRaises(ValueError) as e:
            list(substitute_pattern('{foo}/bar', override_vars=dict(fo0='bar')))

        self.assertIn('\'{foo}/bar\'', str(e.exception))
        self.assertIn('\'foo\'', str(e.exception))


if __name__ == '__main__':
    unittest.main()
