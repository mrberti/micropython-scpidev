try:
    import logging
except ImportError:
    import scpidev.logging_mockup as logging
import time
import threading
import scpidev

FORMAT = "%(levelname)s: %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
# logging.basicConfig(format=FORMAT, level=logging.INFO)

# Define our callback functions
def test_function(*args, **kwargs):
    print("## Execute. ##")
    i = 0
    for arg in args:
        time.sleep(1)
        i += 1
        print("Got arg: {}".format(str(arg)))
    return i

def test_function2(test):
    print("## Execute. ##" + str(test))

# Define some test command strings
command_strings = [
    # "*RST",
    # "*IDN?",
    "MEASure:CURRent[:DC]? [{<range>|AUTO|MIN|MAX|DEF} [,{<resolution>|MIN|MAX|DEF}] ]",
    "MEASure[:VOLTage][:DC]? [{<range>|AUTO|MIN|MAX|DEF} [,{<resolution>|MIN|MAX|DEF}] ]",
    "[SENSe:]VOLTage[:DC]:NULL[:STATe] {ON|OFF}",
    ":VOLTage[:DC]:NULL[:STATe] {ON|OFF}",
    "CALCulate:FUNCtion {NULL | DB | DBM | AVERage | LIMit}",
    """
    MEASure[:VOLTage][:DC]?
        [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}] ]
    """,
]

# # Define some test commands, which will be sent to our device
# test_commands = [
#     # "*RST",
#     # "*IDN?",
#     "CONF AUTO",
#     "MEAS:CURREnt? 10 A, MAX",
#     "XXX?",
# ]

# # Create the instance of our SCPI device
# dev = scpidev.SCPIDevice(
#     name="My SCPI Device",
# )

# # Create commands
# for cmd in command_strings:
#     dev.add_command(
#         scpi_string=cmd,
#         callback=test_function,
#     )

# # Crate the communication interfaces
# # dev.create_interface("tcp")
# dev.create_interface("udp")
# # dev.create_interface("serial", port="COM7", baudrate="500000", dsrdtr=1)

# t = threading.Thread(target=dev.run)
# t.start()
# time.sleep(5)
# dev.stop()
# t.join()
# exit()

# # try:
# #     dev.run()
# # except KeyboardInterrupt:
# #     dev.stop()
# #     exit()

# print("\n-- LIST COMMANDS: -------")
# print(dev.list_commands())


# print("\n-- EXECUTE: -------------")

# for cmd_str in test_commands:
#     print(cmd_str)
#     dev.execute(cmd_str)

# print("\n-- COMMAND HISTORY: ------")
# for c in dev.get_command_history():
#     print(c)

# print("\n-- ALARMS: --------------")
# while True:
#     alarm = dev.get_last_alarm()
#     if alarm is None:
#         break
#     print(alarm)
