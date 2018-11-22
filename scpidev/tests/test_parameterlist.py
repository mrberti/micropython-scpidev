import logging

import scpidev

FORMAT = "<%(levelname)s> %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)


# Define test strings.
ps = [
    "[{<range>|AUTO|MIN|MAX|DEF} [,  {<resolution>|MIN|MAX|DEF}] ]",
    "{<test_type>|DEF}",
    "{NULL | DB | DBM | AVERage | LIMit}",
    "{REQuired|OPTional}",
    "{<date string>|CHANnel<n>}",
    "",
    """
    [<interval>{CYCLe | DISPlay}]
    [,]
    [<type>{AC | DC}]
    [,]
    [<source>{CHANnel<n> | FUNCtion | MATH | WMEMory<r>}]
"""
]

for p in ps:
    pl = scpidev.SCPIParameterList(p)
    for param in pl:
        print(param)
    print("--------------------------")