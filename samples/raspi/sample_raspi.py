import logging
import time
import threading
import os

import scpidev


FORMAT = "%(levelname)s: %(message)s"
# logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logging.basicConfig(format=FORMAT, level=logging.INFO)


# Define the action function
def ieee488_idn(*args, **kwargs):
    return "SCPIDevice,0.0.1a"

def ieee488_rst(*args, **kwargs):
    pass

def ieee488_cls(*args, **kwargs):
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

def syst_help(*args, **kwargs):
    cmd_list = dev.get_command_list()
    cmd_list.sort()
    result = "\n"
    for cmd in cmd_list:
        result = result + str(cmd) + "\n"
    return scpidev.utils.create_block_data_string(result)

def syst_err(*args, **kwargs):
    return "'" + str(dev.get_alarm()) + "'"

def main():
    # Define the test command dictionary
    cmd_dict = {
        "MEASure:TEMPerature[:CORE]?": meas_temp_core,
        "MEASure:CLOCK:ARM?": meas_clock_arm,
        "MEASure:CLOCK:CORE?": meas_clock_core,
        "SYSTem:HELP?": syst_help,
        "SYSTem:ERRor[:NEXT]?": syst_err,
    }

    # Create the instance of our SCPI device. It should be global, so that the 
    # action functions will be able to control the internal states, like alarm.
    global dev
    dev = scpidev.SCPIDevice(cmd_dict=cmd_dict)

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
            time.sleep(1)
    except KeyboardInterrupt:
        dev.stop()

if __name__ == "__main__":
    main()
