import unittest
import scpidev.utils as utils

class TestUtils(unittest.TestCase):
    def test_regexps(self):
        pass

    def test_findfirst(self):
        pass

    def test_remove_non_ascii(self):
        pass

    def test_sanitize(self):
        pass

    def test_create_keyword_string(self):
        pass

    def test_create_parameter_string(self):
        pass

    def test_get_local_ip(self):
        # This should fail and thus the default value should be used.
        ip = utils.get_local_ip("255.255.255.255",default_ip="localhost")
        self.assertEqual(ip, "localhost")

        # This should success and thus the result should differ from the
        # default value.
        ip = utils.get_local_ip(default_ip="localhost")
        self.assertNotEqual(ip, "localhost")

if __name__ == "__main__":
    unittest.main()
