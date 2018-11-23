import logging

import scpidev

FORMAT = "%(levelname)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)

# Define test strings.
ps = [
    # "{<resolution>|MIN|MAX|DEF}",
    # "{<test_type>|DEF}",
    "{0|1|OFF|ON}",
    # "{REQuired|OPTional}",
    # "{<date string>|CHANnel<n>}",
    # "",
]

for p in ps:
    vl = scpidev.SCPIValueList(p)
    print("Value string: {}".format(repr(p)))
    for v in vl:
        print(v)
    print("-----------------------------")
