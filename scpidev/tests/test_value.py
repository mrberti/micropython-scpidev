import unittest
from scpidev.value import SCPIValue, SCPIValueList

class TestSCPIValue(unittest.TestCase):
    # Define test strings.
    ps = [
        "{<resolution>|MIN|MAX|DEF}",
        "{<test_type>|DEF}",
        "{0|1|OFF|ON}",
        # None,
        # "{REQuired|OPTional}",
        # "{<date string>|CHANnel<n>}",
        # "",
    ]

    def setUp(self):
        print("Starting Value test")

    def test(self):
        for p in TestSCPIValue.ps:
            vl = SCPIValueList(p)
            print("Value string: {}".format(repr(p)))
            for v in vl:
                print(v)
            print("-----------------------------")
        pass

if __name__ == "__main__":
    unittest.main()
