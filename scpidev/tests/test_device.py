import logging
import scpidev

FORMAT = "%(levelname)s: %(message)s"
# logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logging.basicConfig(format=FORMAT, level=logging.INFO)

def test_function(*args, **kwargs):
    print("## Execute. ##")
    for arg in args:
        print("Got arg: {}".format(str(arg)))

def test_function2(test):
    print("## Execute. ##" + str(test))

command_strings = [
    # "*RST",
    # "*IDN?",
    "MEASure:CURRent[:DC]? [{<range>|AUTO|MIN|MAX|DEF} [,{<resolution>|MIN|MAX|DEF}] ]",
    "[SENSe:]VOLTage[:DC]:NULL[:STATe] {ON|OFF}",
    ":VOLTage[:DC]:NULL[:STATe] {ON|OFF}",
    "CALCulate:FUNCtion {NULL | DB | DBM | AVERage | LIMit}",
    """
    MEASure[:VOLTage][:DC]? 
        [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}] ]
    """,
]

test_commands = [
    # "*RST",
    # "*IDN?",
    "CONF AUTO",
    "MEAS:CURREnt? 10 A, MAX",
    "XXX?",
]

dev = scpidev.SCPIDevice(
    name="My SCPI Device",
)

for cmd in command_strings:
    dev.add_command(
        scpi_string=cmd,
        callback=test_function2,
    )

print("\n-- LIST COMMANDS: -------")
print(dev.list_commands())


print("\n-- EXECUTE: -------------")

for cmd_str in test_commands:
    print(cmd_str)
    dev.execute(cmd_str)

print("\n-- COMMAND HISTORY: ------")
for c in dev.get_command_history():
    print(c)

print("\n-- ALARMS: --------------")
while True:
    alarm = dev.get_last_alarm()
    if alarm is None:
        break
    print(alarm)
