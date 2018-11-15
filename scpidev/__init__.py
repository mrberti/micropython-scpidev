from scpidevice import SCPIDevice
from scpiparser import SCPIParser
from scpicommand import SCPICommand

if __name__ == "__main__":
    dev = SCPIDevice()
    par = SCPIParser()
    cmd = SCPICommand()