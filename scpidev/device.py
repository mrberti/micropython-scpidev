import logging
import threading
import time

from . import utils
from .command import SCPICommand, SCPICommandList
from .interface import SCPIInterface

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
        during execution, they are catched and an alarm is set."""
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
                        "Exception during execution of function '{}': {}."
                        .format(fn_name, str(e)))
                    break
                cmd_hist_string = "'{cs}' => '{cmd}' => {fn} => {res}".format(
                    cs=command_string, cmd=str(cmd), fn=fn_name, 
                    res=str(result))
                self._command_history.append(cmd_hist_string)
                executed = True
                break

        if not executed:
            if not match_found:
                reason = "No match found."
            self.set_alarm("Could not execute command '{c}'. {r}"
                .format(c=str(command_string), r=reason))
        return result

    def get_command_history(self):
        """Return a list which contains all succesfully executed commands."""
        return self._command_history

    def create_interface(self, type, *args, **kwargs):
        type = type.lower()
        interface = SCPIInterface(type, *args, **kwargs)
        self._interface_list.append(interface)

    def run(self):
        self._thread_list = list()
        self._data_received_event = threading.Event()
        self._event_connection_closed = threading.Event()
        # The _data_recv variable is secured by a thread lock. Always use the 
        # read and write handler to insure data consistency.
        self._data_recv = list()
        self._lock = threading.Lock()

        watchdog_thread = threading.Thread(
            target=self._watchdog, name="Watchdog")
        watchdog_thread.daemon = True
        watchdog_thread.start()

        if not self._interface_list:
            raise Exception("Cannot run: No interface specified.")

        for interface in self._interface_list:
            thread_name = str(interface)
            args = (interface, self._data_received_event)
            t = threading.Thread(
                target=self._data_handler, name=thread_name, args=args)
            self._thread_list.append(t)
            t.daemon = True
            t.start()

        while not self._event_connection_closed.is_set():
            self._data_received_event.wait()
            self._data_received_event.clear()
            data_recv = self._read_data_from_buffer()
            for command_string in data_recv:
                self.execute(command_string)
            print(data_recv)
            time.sleep(1.)
        print("Server stopped...")

    def stop(self):
        self._event_connection_closed.set()

    def _data_handler(self, interface, data_received_event):
        while True:
            try:
                interface.open()
            except Exception as e:
                logging.warning(
                    "Could not open interface {}. Exception: {}"
                    .format(interface, str(e)))
                return

            while True:
                data_recv = interface.readline()
                if not data_recv:
                    break
                # print(repr(data_recv))
                self._append_data_to_buffer(data_recv)
                data_received_event.set()
                
                interface.write(data_recv)
            interface.close()
            time.sleep(1)

    # def _write_data_to_buffer(self, data):
    #     self._lock.acquire()
    #     self._data_recv = data
    #     self._lock.release()

    def _append_data_to_buffer(self, data):
        self._lock.acquire()
        self._data_recv.append(data)
        self._lock.release()

    def _read_data_from_buffer(self):
        self._lock.acquire()
        data = self._data_recv
        self._lock.release()
        return data

    def _watchdog(self):
        """The watchdog should periodically check for deadlocks or other 
        inconsistencies. Todo: implement."""
        while True:
            logging.debug("Watchdog alive.")
            time.sleep(10)
