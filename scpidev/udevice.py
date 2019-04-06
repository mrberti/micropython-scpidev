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
            else:
                print("Parameter mismatch.")
        else:
            print("No match found.")
        return result_string

    def poll(self, *args, **kwargs):
        result_list = list()
        data_str_recv = self._interface.recv(timeout=3)
        if data_str_recv:
            cmd_str_list_recv = data_str_recv.split()
            if not data_str_recv.endswith("\n"):
                del cmd_str_list_recv[-1]
            if cmd_str_list_recv:
                for cmd_str in cmd_str_list_recv:
                    result = self.execute(cmd_str)
                    if result:
                        result_list.append(result)
                        try:
                            self._interface.write(str(result))
                            print("{!r}".format(result))
                        except Exception as exc:
                            print("Could not send data. {}.".format(exc))
                self._interface.close_remote()
        return (data_str_recv, result_list)

    def close(self):
        print("Closing device...")
        self._interface.close()
