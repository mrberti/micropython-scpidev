import logging
import threading
import time
try:
    from queue import Queue, Empty
except ImportError:
    # Python2 compatibility
    from Queue import Queue, Empty

from . import utils
from .command import SCPICommand, SCPICommandList
from .interface import SCPIInterfaceTCP, SCPIInterfaceUDP, SCPIInterfaceSerial

class SCPIDevice():
    """``SCPIDevice`` is the main class for the SCPI device. It contains a 
    list with all valid commands. Each command requires a callback function to 
    be set. It will be called when ``SCPIDevice.execute(cmd_string)`` is 
    and a matching command could be found."""

    def __init__(self, name=""):
        """Todo: Add more parameters, e.g. *IDN strings"""
        self._command_list = SCPICommandList()
        self._alarm_state = False
        self._alarm_trace = list()
        self._command_history = list()
        self._interface_list = list()

    def get_command_list(self):
        """Return a list of command objects."""
        return self._command_list

    def add_command(self, scpi_string, callback, name="", description=""):
        """Add a command string and an associated callback."""
        new_cmd = SCPICommand(
            scpi_string=scpi_string,
            callback=callback,
            name=name,
            description=description,
        )
        self._command_list.append(new_cmd)

    def list_commands(self):
        """Return a list of command strings which were added to the device."""
        commands = list()
        for cmd in self.get_command_list():
            commands.append(str(cmd))
        return commands

    def set_alarm(self, message):
        """Set an alarm with the content of ``message``."""
        alarm_string = message
        self._alarm_state = True
        self._alarm_trace.append(alarm_string)
        logging.info(alarm_string)

    def get_last_alarm(self, clear_alarm_when_empty=True):
        """Return the most recent alarm and remove it from the alarm trace. If 
        ``clear_alarm_when_empty`` is True, the alarm status will be cleared 
        if all alarms got consumed."""
        if self._alarm_trace:
            alarm = self._alarm_trace.pop()
            if alarm is None and clear_alarm_when_empty:
                self._alarm_state = False
            return alarm
        else:
            return None

    def clear_alarm(self, clear_history=True):
        """Confirm an alarm. If ``clear_history`` is True, the alarm history 
        will also be cleared. Attention: All previous alarms will be lost in 
        that case."""
        self._alarm_state = False
        if clear_history:
            self._alarm_trace = list()

    def execute(self, command_string):
        """Search a matching command and execute it. If exceptions arise 
        during execution, they are catched and an alarm is set.
        
        Todo: 
        - Implement multiple commands in one line, e.g. MEAS?;MEAS:CURR?\n
        - Implement parallelism in execution tasks
        """
        executed = False
        match_found = False
        result = None
        reason = "No reason."
        for cmd in self.get_command_list():
            if cmd.match(command_string):
                match_found = True
                fn_name = cmd.get_callback().__name__
                parameter_string = utils.create_parameter_string(
                    command_string)
                try:
                    result = cmd.execute(parameter_string)
                except Exception as e:
                    reason = (
                        "Exception during execution of function {}: {}."
                        .format(repr(fn_name), str(e)))
                    break
                cmd_hist_string = "{cs} => {cmd} => {fn} => {res}".format(
                    cs=repr(command_string), cmd=repr(cmd), fn=fn_name, 
                    res=repr(result))
                self._command_history.append(cmd_hist_string)
                executed = True
                break

        if not executed:
            if not match_found:
                reason = "No match found."
            self.set_alarm("Could not execute command {c}. {r}"
                .format(c=repr(command_string), r=reason))
        return result

    def get_command_history(self):
        """Return a list which contains all succesfully executed commands."""
        return self._command_history

    def create_interface(self, type, *args, **kwargs):
        """Create a communication interface.

        Currently, these types are supported:
        - TCP
        - UDP
        - Serial
        """
        type = type.lower()
        if type == "tcp":
            interface = SCPIInterfaceTCP(*args, **kwargs)
        elif type == "udp":
            interface = SCPIInterfaceUDP(*args, **kwargs)
        elif type == "serial":
            interface = SCPIInterfaceSerial(*args, **kwargs)
        self._interface_list.append(interface)

    def run(self):
        """Start listening on the previously created interfaces and execute 
        commands when a message is received.

        This function should usually run forever.

        Todo:
        - Implement parallel execution tasks
        """
        self._thread_list = list()
        self._recv_queue = Queue() # Todo: Maxsize

        self.start_watchdog()

        if not self._interface_list:
            raise Exception("Cannot run: No interface specified.")

        for interface in self._interface_list:
            args = (self._recv_queue,)
            t = threading.Thread(
                target=interface.data_handler, name=str(interface), args=args)
            self._thread_list.append(t)
            t.daemon = True
            t.start()

        while True:
            time.sleep(1)
            while True:
                try:
                    data_recv = self._recv_queue.get(timeout=1)
                except Empty:
                    continue
                break
            interface = data_recv[0]
            command_string = data_recv[1]
            result = self.execute(command_string)
            # Todo: return data
            if result is not None:
                interface.write(str(result))

        print("Server stopped...")

    def start_watchdog(self):
        # Todo: implement an intelligent watchdog
        watchdog_thread = threading.Thread(
            target=self._watchdog_handler, name="Watchdog")
        watchdog_thread.daemon = True
        watchdog_thread.start()

    def _watchdog_handler(self):
        """The watchdog should periodically check for deadlocks or other 
        inconsistencies. Todo: implement."""
        while True:
            logging.debug("Watchdog alive.")
            time.sleep(100)
