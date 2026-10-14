import unittest

import quietwriter


class PackageMetadataTests(unittest.TestCase):
    def test_app_name_is_available_for_app_imports(self):
        self.assertEqual(quietwriter.APP_NAME, 'QuietWriter')

    def test_version_is_current(self):
        self.assertTrue(quietwriter.__version__.startswith('1.5.0-dev.'))


if __name__ == '__main__':
    unittest.main()
