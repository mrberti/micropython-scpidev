try:
    import time
except ImportError:
    import utime as time

from scpidev.udevice import SCPIDevice

try:
    from machine import Pin
    import onewire
    import ds18x20
    def init_hardware():
        global ow, ds, roms
        ow = onewire.OneWire(Pin(14)) # GPIO14 = D5 on weemos D1
        ds = ds18x20.DS18X20(ow)
        roms = ds.scan()
except:
    def init_hardware():
        print("Warning: Using mockup init_hardware()")

# Define the action function
def idn(*args, **kwargs):
    return "micropython-scpidev,0.0.1a"

def rst(*args, **kwargs):
    pass

def meas_temp(*args, **kwargs):
    temp = "-999"
    try:
        ds.convert_temp()
        time.sleep_ms(750)
        temp = str(ds.read_temp(roms[0]))
    except:
        time.sleep(2)
        print("Warning: Could not convert temp")
    return temp

def main():
    init_hardware()

    # Define the test command dictionary
    cmd_dict = {
        "MEASure[:TEMPerature]?": meas_temp,
    }

    # Create the instance of our SCPI device. It should be global, so that the
    # action functions will be able to control the internal states, like alarm.
    global dev
    dev = SCPIDevice(
        cmd_dict=cmd_dict,
        interface="tcp",
        buffer_size=128,
    )

    # Add some standard commands
    dev.add_command("*IDN?", idn)
    dev.add_command("*RST", rst)

    # Crate the communication interfaces
    # dev.create_interface("tcp", buffer_size=1024, timeout=1)

    # Start the server thread and wait until program is terminated (ctrl+c).
    try:
        while True:
            print(repr(dev.poll()))
    # except (KeyboardInterrupt,Exception) as exc:
    except KeyboardInterrupt as exc:
        print("Stopping... {}".format(exc))
    finally:
        dev.close()

if __name__ == "__main__":
    main()
