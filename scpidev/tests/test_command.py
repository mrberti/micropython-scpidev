import logging
import re

import scpidev

FORMAT = "<%(levelname)s> %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


def test_function(*args, **kwargs):
    for arg in args:
        print("Test function, {}".format(str(arg)))

cmd_str = ("MEASure[:VOLTage][:DC]? "
    "[{<range>|AUTOmatic|MIN|MAX|DEF} [,  {<resolution>|MIN|MAX|DEF}] ]")
cmd = scpidev.SCPICommand(cmd_str, test_function)
k = "measu?"
parameters = [
    "10 A",
    "AUTO, MIN",
    "asd",
]

for p in parameters:
    c = k + p
    cmd.execute_if_match(p)
    print("--------------------------")
