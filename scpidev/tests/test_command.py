import unittest
import re
from scpidev.command import SCPICommand, SCPICommandList

def test_function(*args, **kwargs):
    for arg in args:
        print("Test function, {}".format(str(arg)))

class TestSCPICommand(unittest.TestCase):
    def setUp(self):
        pass

    def test(self):
        cmd_str = ("MEASure[:VOLTage][:DC]? "
            "[{<range>|AUTOmatic|MIN|MAX|DEF} [,  {<resolution>|MIN|MAX|DEF}] ]")
        cmd = SCPICommand(cmd_str, test_function)
        k = "measu?"
        parameters = [
            "10 A",
            "AUTO, MIN",
            "asd",
        ]

        for p in parameters:
            c = k + p
            cmd.execute_if_match(p)

if __name__ == "__main__":
    unittest.main()
