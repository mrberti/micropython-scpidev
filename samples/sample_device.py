import logging
import time
import threading

import scpidev

def main():
    FORMAT = "%(levelname)s: %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    # logging.basicConfig(format=FORMAT, level=logging.INFO)

    # Define our action functions
    def test_function(*args, **kwargs):
        print("## Execute: {} ##".format(repr(kwargs["command_string"])))
        i = 0
        for arg in args:
            print("Got arg {}: {}".format(str(i), repr(arg)))
            i += 1
        return i

    def malfunction(*args, **kwargs):
        """A malfunctioning function to test exception handling."""
        return args[999]

    def idn(*args, **kwargs):
        return "SCPIDevice,0.0.1a"

    def rst(*args, **kwargs):
        print("Clear device history")
        dev.clear_alarm(clear_history=True)

    # Define some test command strings
    command_strings = [
        "MEASure:CURRent[:DC]? [{<range>|AUTO|MIN|MAX|DEF} "
            "[,{<resolution>|MIN|MAX|DEF}] ]",
        "MEASure[:VOLTage][:DC]? [{<range>|AUTO|MIN|MAX|DEF} "
            "[,{<resolution>|MIN|MAX|DEF}] ]",
        "[SENSe:]VOLTage[:DC]:NULL[:STATe] {ON|OFF}",
        ":VOLTage[:DC]:NULL[:STATe] {ON|OFF}",
        "CALCulate:FUNCtion {NULL | DB | DBM | AVERage | LIMit}",
        """
        MEASure[:VOLTage][:DC]? 
            [{<range>|AUTO|MIN|MAX|DEF} [, {<resolution>|MIN|MAX|DEF}] ]
        """,
    ]

    # Create the instance of our SCPI device
    dev = scpidev.SCPIDevice()

    # Create commands
    dev.add_command("*IDN?", idn)
    dev.add_command("*RST", rst)
    for cmd in command_strings:
        dev.add_command(
            scpi_string=cmd,
            action=test_function,
        )
    dev.add_command("MALfunction", malfunction)

    # Crate the communication interfaces
    dev.create_interface("tcp")
    dev.create_interface("udp")
    dev.create_interface("serial", port="COM7", baudrate="500000", dsrdtr=1)

    # Start the server thread and wait until the user terminates this program 
    # by ctrl+c.
    dev.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dev.stop()

if __name__ == "__main__":
    main()
