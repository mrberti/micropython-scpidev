import logging
import re

import scpidev


logging.basicConfig(level=logging.DEBUG)

def test_function(**kwargs):
    pass
    # print("Test function, {}".format(str(kwargs)))

cmd_str = "MEASure[:VOLTage][:DC]? [{<range>|AUTO|MIN|MAX|DEF} [,  {<resolution>|MIN|MAX|DEF}] ]"
cmd = scpidev.SCPICommand(cmd_str, test_function)

print("")
cmd_str = "CALCulate:FUNCtion {NULL | DB | DBM | AVERage | LIMit}"
cmd = scpidev.SCPICommand(cmd_str, test_function)

"""
:MEASure:VRMS 
    [<interval>{CYCLe | DISPlay}]
    [,]
    [<type>{AC | DC}]
    [,]
    [<source>{CHANnel<n> | FUNCtion | MATH | WMEMory<r>}]
"""

"""
MEASure[:VOLTage][:DC]? 
    [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}] ]
"""
