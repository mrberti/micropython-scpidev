"""
An absolute minimal implementation of SCPIDevice to run on smaller
MicroPython devices.

>>> from scpidev.udevice import SCPIDevice

You will have to `poll()` on your interface in a loop yourself. During
the execution of commands, new connections will be blocked.
"""
try:
    import utime as time
except ImportError:
    import time
from .command import SCPICommand, SCPICommandList
from .uinterface import SCPIInterfaceTCP
import os
import binascii


BUFFER_SIZE = 128


class SCPIDevice():
    def __init__(self, *args, **kwargs):
        self._command_list = SCPICommandList()
        self._interface = None
        if "interface" in kwargs:
            self.create_interface(kwargs["interface"], *args, **kwargs)
        if "cmd_dict" in kwargs:
            for cmd_string in kwargs["cmd_dict"]:
                self.add_command(
                    cmd_string,
                    kwargs["cmd_dict"][cmd_string],
                )
        self.reset_error_message()
        self.status_byte = 0x00
        self.sre = 0
        
        self._add_standard_commands()
        
    def _add_standard_commands(self):
        self.add_command('*IDN', self.idn)
        self.add_command('*CLS', self.reset_error_message)
        self.add_command(':SYSTem:ERRor?', self.get_error_message)
        self.add_command('*SRE', self.set_service_request_enable)
        self.add_command('*SRE?', self.get_service_request_enable)
        self.add_command('*STB?', self.get_status_byte)
        
    def set_service_request_enable(self, *args, **kwargs):
        self.sre = int(args[0])
    
    def get_service_request_enable(self, *args, **kwargs):
        return self.sre
    
    def get_status_byte(self, *args, **kwargs):
        return self.status_byte
        
    def idn(self, *args, **kwargs):
        # args and kwargs for compatiblity with self.execute
        machine_name = os.uname().sysname
        mac = binascii.hexlify(nic.config('mac')).decode()
        return "micropython-scpidev,{},{},0.0.1a".format(machine_name, mac)
        
    def reset_error_message(self, *args, **kwargs):
        # args and kwargs for compatiblity with self.execute
        self.last_error_message = "0 No error"
        
    def get_error_message(self, *args, **kwargs):
        # args and kwargs for compatiblity with self.execute
        return self.last_error_message
    
    def get_status_byte(self, *args, **kwargs):
        return self.status_byte
    
    def add_command(self, scpi_string, action, name="", description=""):
        new_cmd = SCPICommand(
            scpi_string=scpi_string,
            action=action,
            name=name,
            description=description,
        )
        self._command_list.append(new_cmd)

    def create_interface(self, type, *args, **kwargs):
        if "tcp" in type.lower():
            self._interface = SCPIInterfaceTCP(*args, **kwargs)
        else:
            raise NotImplementedError(type)

    def execute(self, command_string):
        result_string = None
        if not command_string:
            return result_string
        # command_string = utils.sanitize(command_string)
        cmd = self._command_list.get_command(command_string,
            match_parameters=False)
        if cmd:
            if self._command_list.get_command(command_string,
                    match_parameters=True) is not None:
                try:
                    result = cmd.execute(command_string)
                    if result is not None:
                        result_string = str(result)
                        if not result_string.endswith("\n"):
                            result_string = result_string + "\n"
                except Exception as exc:
                    print(
                        "Exception during execution of function {!r}: {}."
                        .format(command_string, exc))
                    raise exc
            else:
                self.last_error_message = '1 parameter missmatch'
                print("Parameter mismatch.")
        else:
            self.last_error_message = f'1 command "{command_string}" not found'
            print("No match found.")
        return result_string

    def poll(self, *args, **kwargs):
        result_list = list()
        data_str_recv = self._interface.recv()
        if data_str_recv:
            cmd_str_list_recv = data_str_recv.split(";")
            if not data_str_recv.endswith("\n"):
                del cmd_str_list_recv[-1]
            if cmd_str_list_recv:
                for cmd_str in cmd_str_list_recv:
                    try:
                        result = self.execute(cmd_str)
                    except Exception as err:
                        result = None
                        self.last_error_message = f'1 {err}'
                        
                    if result:
                        result_list.append(result)
                        try:
                            self._interface.write(str(result))
                        except Exception as exc:
                            print("Could not send data. {}.".format(exc))
        return (data_str_recv, result_list)

    def close(self):
        print("Closing device...")
        self._interface.close()
