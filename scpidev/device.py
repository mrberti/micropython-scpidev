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
        self._command_history = list()
        self._alarm_state = False
        self._alarm_trace = list()
        self._interface_list = list()
        self._interface_type_list = list()
        self._is_running = threading.Event()
        self._watchdog_running = threading.Event()

    def get_command_list(self):
        """Return a list of command objects."""
        return self._command_list

    def get_command_history(self):
        """Return a list which contains all succesfully executed commands."""
        return self._command_history

    def add_command(self, scpi_string, action, name="", description=""):
        """Add a command string and an associated action."""
        new_cmd = SCPICommand(
            scpi_string=scpi_string,
            action=action,
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

    def get_alarm(self, clear_alarm_when_empty=True):
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

    def create_interface(self, type, *args, **kwargs):
        """Create a communication interface. The actual instantiation will be 
        done when the interface is actually needed. The application programmer 
        needs to make sure that assigning the same resource more than 1 time 
        is avoided.

        Currently, these types are supported:
        - TCP
        - UDP
        - Serial (not yet implemented)
        """
        type = type.lower()
        # The interfaces will only be defined here. The instantiation will 
        # happen later when ``run()`` is called. This insures that after 
        # multiple ``run()`` calls new interfaces are instantiated.
        interface_type = (type, args, kwargs)
        self._interface_type_list.append(interface_type)

    def _instantiate_interface(self, type, *args, **kwargs):
        if type == "tcp":
            interface = SCPIInterfaceTCP(*args, **kwargs)
        elif type == "udp":
            interface = SCPIInterfaceUDP(*args, **kwargs)
        elif type == "serial":
            interface = SCPIInterfaceSerial(*args, **kwargs)
        return interface

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
        command_string = utils.sanitize(command_string)
        for cmd in self.get_command_list():
            if cmd.match(command_string):
                match_found = True
                fn_name = cmd.get_action_name()
                try:
                    result = cmd.execute(command_string)
                except Exception as e:
                    reason = (
                        "Exception during execution of function {}: {}."
                        .format(repr(fn_name), str(e)))
                    break
                cmd_hist_string = "{cs} => {fn} => {res}".format(
                    cs=repr(command_string), fn=fn_name, 
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

    def run(self):
        """Start listening on the previously by ``create_interface()`` defined 
        interfaces and execute commands when a message is received. This 
        function will run until ``stop()`` is called.

        Todo:
        - Implement parallel execution tasks
        """
        self._recv_queue = Queue() # Todo: Maxsize
        self._thread_list = list()
        self._interface_list = list()

        if not self._interface_type_list:
            logging.error("Cannot run: No interfaces were specified.")
            return

        self.start_watchdog()

        # Instantiate the interfaces.
        for interface_type in self._interface_type_list:
            type = interface_type[0]
            args = interface_type[1]
            kwargs = interface_type[2]
            try:
                interface = self._instantiate_interface(type, args, kwargs)
                self._interface_list.append(interface)
            except Exception as e:
                logging.error("Could not instantiate interface '{}'. "
                    "Exception: {}".format(interface_type, e))
        logging.debug("Instantiated {} interfaces.".format(
            len(self._interface_list)))

        # Create threads for each interface's data handler.
        for interface in self._interface_list:
            args = (self._recv_queue,)
            t = threading.Thread(
                target=interface.data_handler, name=str(interface), args=args)
            self._thread_list.append(t)
            # t.daemon = True
            t.start()

        # As long as we did not receive a stop command, we try to get the data 
        # from the receive queue and execute a command.
        self._is_running.set()
        while self._is_running.is_set():
            # Get data from the queue which will be written by the interface
            # data handlers.This timeout -> continue loop is necessary because 
            # otherwise, Queue.get() would block KeyboardInterrupts.
            while self._is_running.is_set():
                try:
                    data_recv = self._recv_queue.get(timeout=1)
                except Empty:
                    continue
                break

            # Execute the received command string and return the result (if 
            # any).
            if self._is_running.is_set():
                interface = data_recv[0]
                command_string = data_recv[1]
                result = self.execute(command_string)
                if result is not None:
                    try:
                        interface.write(str(result))
                    except Exception as e:
                        logging.info("Could not send data to {}.  Exception: "
                        "{}.".format(str(interface), str(e)))

        # Do not forget to clean-up.
        self.stop_watchdog()
        logging.debug("'run()' has finished.")

    def stop(self, timeout=None):
        self._is_running.clear()
        for interface in self._interface_list:
            interface.stop()
        for thread in self._thread_list:
            logging.debug("Waiting for Thread '{}' to finish."
                .format(thread.name))
            thread.join(timeout=timeout)
        logging.debug("All data handlers have finished.")

    def start_watchdog(self):
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_handler, name="Watchdog")
        self._watchdog_thread.daemon = False
        self._watchdog_running.set()
        self._watchdog_thread.start()

    def stop_watchdog(self):
        self._watchdog_running.clear()
        self._watchdog_thread.join()

    def _watchdog_handler(self):
        """The watchdog should periodically check for deadlocks or other 
        inconsistencies. Todo: implement."""
        # Todo: implement an intelligent watchdog
        iterations = 0
        while self._watchdog_running.is_set():
            if iterations < 10:
                iterations += 1
            else:
                logging.debug("{}: Watchdog alive. Alarms: {}."
                    .format(time.time(), len(self._alarm_trace)))
                iterations = 0
            time.sleep(1)
        logging.info("Watchdog has stopped.")
