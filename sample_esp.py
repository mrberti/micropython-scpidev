"""
This script runs an SCPI server on an ESP8266 board with MicroPython
installed.

Put as `main.py` into the top level directory of your ESP8266 board.
"""
import gc
import binascii
try:
    import time
    import os
except ImportError:
    import utime as time
    import uos as os

from scpidev.udevice import SCPIDevice

try:
    from machine import Pin, ADC, reset
    import network
    import onewire
    import ds18x20
    def init_hardware():
        global sta_if, ow, ds, roms, adc0, led
        print("Activating Wifi...")
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        while not sta_if.isconnected():
            time.sleep(.1)
        print("Wifi activated: {}. MAC={}".format(
            sta_if.ifconfig(),
            binascii.hexlify(sta_if.config("mac")).decode()))
        ow = onewire.OneWire(Pin(14)) # GPIO14 = D5 on weemos D1
        ds = ds18x20.DS18X20(ow)
        roms = ds.scan()
        adc0 = ADC(0)
        led = Pin(2, Pin.OUT)
        led.on() # On wemos D1 board inverted logic
except ImportError:
    def init_hardware():
        print("Warning: Using mockup init_hardware()")

# Define the action function
def idn(*args, **kwargs):
    machine_name = os.uname()[0]
    mac = binascii.hexlify(sta_if.config("mac")).decode()
    return "micropython-scpidev,{},{},0.0.1a".format(machine_name, mac)

def rst(*args, **kwargs):
    dev.close()
    raise Exception("Resetting device")

def meas_temp(*args, **kwargs):
    temp = "-999"
    print("Measure temperature...")
    try:
        led.off()
        ds.convert_temp()
        time.sleep_ms(750)
        temp = str(ds.read_temp(roms[0]))
        led.on()
    except Exception as exc:
        print("Exception: {}".format(exc))
        time.sleep(.2)
    return temp

def meas_volt(*args, **kwargs):
    volt = "-999"
    print("Measure voltage on ADC0...")
    try:
        led.off()
        volt = adc0.read()
        led.on()
    except:
        time.sleep(.1)
    return volt

def main():
    init_hardware()

    # Define the test command dictionary
    cmd_dict = {
        "MEASure[:VOLTage]?": meas_volt,
        "MEASure:TEMPerature?": meas_temp,
    }

    # Create the instance of our SCPI device. It should be global, so that the
    # action functions will be able to control the internal states, like alarm.
    global dev, running
    dev = SCPIDevice(
        cmd_dict=cmd_dict,
        interface="tcp",
        buffer_size=128,
        timeout=10,
    )

    # Add some standard commands
    dev.add_command("*IDN?", idn)
    dev.add_command("*RST", rst)

    # Crate the communication interfaces
    # dev.create_interface("tcp", buffer_size=1024, timeout=1)

    # Start the server wait until program is terminated (ctrl+c).
    try:
        while True:
            print(repr(dev.poll()))
    except KeyboardInterrupt as exc:
        print("Stopping...")
        running = False
    except Exception as exc:
        log_string = "{}:EXCEPTION:{}".format(time.time(), exc)
        print(log_string)
        with open("log.txt", "a+") as f:
            f.write(log_string)
    finally:
        dev.close()
    gc.collect()

running = True
while running:
    main()
