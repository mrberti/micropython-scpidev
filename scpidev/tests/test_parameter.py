import unittest
from scpidev.parameter import SCPIParameterList, SCPIParameter

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

class TestSCPIParameter(unittest.TestCase):
    def setUp(self):
        for p in ps:
            self.parameter_list = SCPIParameterList(p)

    def test_parameter_list(self):
        pass
    
    def test_parameter_match(self):
        # print("AUTO" in self.parameter_list)
        print("" in self.parameter_list)
        # for p in self.parameter_list:
        #     print(p.match("AUTO"))


if __name__ == "__main__":
    unittest.main()
