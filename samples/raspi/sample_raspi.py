import logging
import time
import threading
import os

import scpidev


FORMAT = "%(levelname)s: %(message)s"
# logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logging.basicConfig(format=FORMAT, level=logging.INFO)


# Define the action function
def idn(*args, **kwargs):
    return "SCPIDevice,0.0.1a"

def rst(*args, **kwargs):
    print("Clear device history")
    dev.clear_alarm(clear_history=True)

# https://elinux.org/RPI_vcgencmd_usage
def vcgencmd(cmd):
    result_string = None
    cmd_string = "/opt/vc/bin/vcgencmd {}".format(cmd)
    try:
        result_string = os.popen(cmd_string).readline()
        result_string = result_string.split("=")[1]
    except Exception as e:
        dev.set_alarm("Exception {}"
            .format(e))
    return result_string

def meas_temp_core(*args, **kwargs):
    return vcgencmd("measure_temp")

def meas_clock_arm(*args, **kwargs):
    return vcgencmd("measure_clock arm")

def meas_clock_core(*args, **kwargs):
    return vcgencmd("measure_clock core")

def main():
    # Define the test command dictionary
    cmd_dict = {
        "MEASure:TEMPerature[:CORE]?": meas_temp_core,
        "MEASure:CLOCK:ARM?": meas_clock_arm,
        "MEASure:CLOCK:CORE?": meas_clock_core,
    }

    # Create the instance of our SCPI device. It should be global, so that the 
    # action functions will be able to control the internal states, like alarm.
    global dev
    dev = scpidev.SCPIDevice(cmd_dict=cmd_dict)

    # Create the standard commands
    dev.add_command("*IDN?", idn)
    dev.add_command("*RST", rst)

    # Crate the communication interfaces
    dev.create_interface("tcp")

    # Start the server thread and wait until program is terminated (ctrl+c).
    dev.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dev.stop()
    exit()

if __name__ == "__main__":
    main()
