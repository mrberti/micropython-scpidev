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
def meas_temp_core(*args, **kwargs):
    result_string = None
    try:
        result_string = os.popen("/opt/vc/bin/vcgencmd measure_temp").readline()
        result_string = result_string.split("=")[1]
    except Except as e:
        dev.set_alarm("Could not measure core temperature. Exception {}"
            .format(e))
    return result_string

def meas_clock_arm(*args, **kwargs):
    result_string = None
    try:
        result_string = os.popen("/opt/vc/bin/vcgencmd measure_clock arm").readline()
        result_string = result_string.split("=")[1]
    except Except as e:
        dev.set_alarm("Could not measure clock. Exception {}"
            .format(e))
    return result_string

def meas_clock_core(*args, **kwargs):
    result_string = None
    try:
        result_string = os.popen("/opt/vc/bin/vcgencmd measure_clock core").readline()
        result_string = result_string.split("=")[1]
    except Except as e:
        dev.set_alarm("Could not measure clock. Exception {}"
            .format(e))
    return result_string

def main():
    # Define the test command dictionary
    cmd_dict = {
        "MEASure:TEMPerature:CORE?": meas_temp_core,
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
    t = threading.Thread(target=dev.run)
    t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        dev.stop()
    exit()

if __name__ == "__main__":
    main()
