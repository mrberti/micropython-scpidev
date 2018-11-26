import unittest
import re
from scpidev.command import SCPICommand, SCPICommandList

def test_function(*args, **kwargs):
    """This function will just return the amount of given arguments."""
    result = 0
    for arg in args:
        result += 1
    for kwarg in kwargs:
        result += 1
    return result

# Define test vectors
cmd_strings = [
    "MEASure[:VOLTage][:DC]? [{<range>|AUTOmatic|MIN|MAX|DEF} [,  {<resolution>|MIN|MAX|DEF}] ]",
    "MEASure:CURRent[:DC]? [{<range> | AUTOmatic | MIN|MAX|DEF} [,  { <resolution>|MIN|MAX|DEF}] ]",
    "MEASure:CURRent:AC?",
]

# {Command: Expected results tuple}. Each entry corresponds to one cmd_string.
test_commands_dict = {
    "MEAS?": (1, None, None),
    " MEasure?": (1, None, None),
    "measure": (None, None, None),
    "measr?": (None, None, None),
    "meas:curre? 10 A, MAX": (None, 3, None),
    "meas:curre:DC? 10 A, MAX": (None, 3, None),
    "meas:curre:DC? 10 A, MAXi": (None, None, None),
}

class TestSCPICommand(unittest.TestCase):
    def setUp(self):
        self.command_list = SCPICommandList()
        for cmd_string in cmd_strings:
            cmd = SCPICommand(cmd_string, test_function)
            self.command_list.append(cmd)

    def test_execute_if_match(self):
        for cmd_string in test_commands_dict:
            cmd_i = 0
            for cmd in self.command_list:
                expected_result = test_commands_dict[cmd_string][cmd_i]
                result = cmd.execute_if_match(cmd_string)
                cmd_i += 1
                self.assertEqual(result, expected_result)

if __name__ == "__main__":
    unittest.main()
