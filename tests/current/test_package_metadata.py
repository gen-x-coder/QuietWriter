import unittest

import quietwriter


class PackageMetadataTests(unittest.TestCase):
    def test_app_name_is_available_for_app_imports(self):
        self.assertEqual(quietwriter.APP_NAME, 'QuietWriter')

    def test_version_is_current(self):
        self.assertEqual(quietwriter.__version__, '1.3.0-rc1')


if __name__ == '__main__':
    unittest.main()
