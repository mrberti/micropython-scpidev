try:
    import time
    import os
except ImportError:
    import utime as time
    import uos as os

import scpidev
from scpidev.device import SCPIDevice


# Define the action function
def ieee488_idn(*args, **kwargs):
    return "micropython-scpidev,0.0.1a"

def ieee488_rst(*args, **kwargs):
    pass

def ieee488_cls(*args, **kwargs):
    dev.clear_alarm(clear_history=True)

def syst_help(*args, **kwargs):
    cmd_list = dev.get_command_list()
    cmd_list.sort()
    result = "\n"
    for cmd in cmd_list:
        result = result + str(cmd) + "\n"
    return scpidev.utils.create_block_data_string(result)

def syst_err(*args, **kwargs):
    return "'{}'".format(dev.get_alarm())

def meas_temp(*args, **kwargs):
    return "20"

def main():
    # Define the test command dictionary
    cmd_dict = {
        "MEASure[:TEMPerature]?": meas_temp,
    }

    # Create the instance of our SCPI device. It should be global, so that the
    # action functions will be able to control the internal states, like alarm.
    global dev
    dev = SCPIDevice(cmd_dict=cmd_dict)

    # Create the standard commands
    dev.add_command("*IDN?", ieee488_idn)
    dev.add_command("*RST", ieee488_rst)
    dev.add_command("*CLD", ieee488_cls)

    # Crate the communication interfaces
    dev.create_interface("tcp")

    # Start the server thread and wait until program is terminated (ctrl+c).
    dev.start()
    try:
        while True:
            dev.recv()
            time.sleep(1)
    except KeyboardInterrupt:
        # dev.stop()
        pass

if __name__ == "__main__":
    main()
