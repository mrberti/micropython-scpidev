import unittest
from scpidev.value import SCPIValue, SCPIValueList

test_vectors = [
    {
        "value_string": "{<resolution>|MINimum|MAX|DEF}",
        "expected_values_list": [
            "<resolution>", ("MIN", "imum", ""), ("MAX", "", ""), 
            ("DEF", "", "")
        ],
        "match_test": [
            ("MIN", True), ("min", True), ("mini", True), ("minimum", True), 
            ("minimumu", False), ("DEf", True), ("+123.37 A", True),
            (" MIN", False),
        ],
    },
    {
        "value_string": "{0|1|OFF|ON}",
        "expected_values_list": [
            ("0", "", ""), ("1", "", ""), ("OFF", "", ""), ("ON", "", "")
        ],
        "match_test": [
            ("mIn", False),
        ],
    }
]

# # Define test strings.
# "<test>",
# "{<resolution>|MIN|MAX|DEF}",
# "{<test_type>|DEF}",
# "{0|1|OFF|ON}",
# None,
# "{REQuired|OPTional}",
# "{\"<date_string>\"|CHANnel<n>}",
# "",

class TestSCPIValue(unittest.TestCase):
    def test_value_list(self):
        for test_vector in test_vectors:
            print("\n++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            # Get test vector data
            vs = test_vector["value_string"]
            evl = test_vector["expected_values_list"]

            # Create value list from test vector
            vl = SCPIValueList(vs)
            print("{} => {}".format(repr(vs), str(vl)))
            n = 0

            # Test correct tuple creation
            print("\n--- Test correct tuple creation ------------------------")
            for v in vl:
                print("Testing: {} == {}".format(
                    repr(v.get_value()), repr(evl[n])))
                self.assertEqual(v.get_value(), evl[n])
                n += 1

            # Test correct value matching
            print("\n--- Test correct value matching ------------------------")
            for val in test_vector["match_test"]:
                print("Testing ({}): {} in {}"
                    .format(val[1], repr(val[0]), str(vl)))
                result = val[0] in vl
                self.assertEqual(result, val[1])


if __name__ == "__main__":
    unittest.main()
    # vl = SCPIValueList("{<resolution>|MINimum|MAX|DEF}")
    # print(vl)
    # print("mi" in vl)
    # print("min" in vl)
    # print("MiNimum" in vl)
    # print("minimumu" in vl)
