import unittest
from scpidev.parameter import SCPIParameterList, SCPIParameter

class TestSCPIParameter(unittest.TestCase):
    # Define test strings.
    ps = [
        "[{<range>|AUTO|MIN|MAX|DEF} [,  {<resolution>|MIN|MAX|DEF}] ]",
        # "{<test_type>|DEF}",
        # "{NULL | DB | DBM | AVERage | LIMit}",
        # "{REQuired|OPTional}",
        # "{<date string>|CHANnel<n>}",
        # "[]",
    #     """
    #     [<interval>{CYCLe | DISPlay}]
    #     [,]
    #     [<type>{AC | DC}]
    #     [,]
    #     [<source>{CHANnel<n> | FUNCtion | MATH | WMEMory<r>}]
    # """
    ]

    def setUp(self):
        print("Starting Value test")

    def test(self):
        for p in TestSCPIParameter.ps:
            pl = SCPIParameterList(p)
            for param in pl:
                print(str(param))

if __name__ == "__main__":
    unittest.main()
