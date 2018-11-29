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
    "MEASure[:VOLTage][:DC]? [{<range>|AUTOmatic|MIN|MAX|DEF}[,{<resolution>|MIN|MAX|DEF}]]",
    "MEASure:CURRent[:DC]? [{<range>|AUTOmatic|MIN|MAX|DEF}[,{<resolution>|MIN|MAX|DEF}]]",
    "MEASure:CURRent:AC? [{<range>|AUTOmatic|MIN|MAX|DEF}[,{<resolution>|MIN|MAX|DEF}]]",
    "*IDN?",
    "*RST",
]

# {Command: Expected results tuple}. Each entry corresponds to one cmd_string.
test_commands_dict = {
    "MEAS?": (1, None, None, None, None),
    " MEasure?": (1, None, None, None, None),
    "MEAS:VOLT?": (1, None, None, None, None),
    "measure": (None, None, None, None, None),
    "measr?": (None, None, None, None, None),
    "meas:curre:AC? AUTOm": (None, None, 2, None, None),
    "meas:curre? 10 A, MAX": (None, 3, None, None, None),
    "MEASure:CURRent:DC? ,-1e-37 A": (None, 3, None, None, None),
    "meas:curre:DC? 10 A, MAXi": (None, None, None, None, None),
    "*IDN?": (None, None, None, 1, None),
    "*RST": (None, None, None, None, 1),
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
            print("----------------------------------------------------------")
            print("Testing: execute_if_match({})"
                .format(repr(cmd_string)))
            for cmd in self.command_list:
                expected_result = test_commands_dict[cmd_string][cmd_i]
                result = cmd.execute_if_match(cmd_string)
                cmd_i += 1
                print("{} => {}?"
                    .format(str(cmd), expected_result))
                # try:
                self.assertEqual(result, expected_result)
                # except AssertionError as e:
                #     print("## FAIL ## {}".format(str(e)))
                #     raise e
    
    def test_in_commandlist(self):
        print("--------------------------------------------------------------")
        print("test_in_commandlist()")
        print("Command list: \n{}".format(str(self.command_list)))
        for cmd_string in test_commands_dict:
            result = cmd_string in self.command_list
            expected_result = any(test_commands_dict[cmd_string])
            print("Testing: {} in command list == {}? ({})".format(
                repr(cmd_string), repr(expected_result), repr(result)))
            self.assertEqual(result, expected_result)

if __name__ == "__main__":
    unittest.main()
    # s = "MEAS"
    # cmd = SCPICommand(s, test_function)
    # cl = SCPICommandList([cmd])
    # print(cl)
    # print(s in cl)
