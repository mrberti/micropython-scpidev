import logging
import socket
import time
import threading
import abc
import select
try:
    from queue import Queue
except ImportError:
    # Python2 compatibility
    from Queue import Queue
try:
    import serial
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False
    import warnings
    warnings.warn("Could not load ``serial`` package. The serial "
        "communication interface will not work. Try to install the package "
        "with `python -m pip install pyserial`.")

from . import utils


class SCPIInterfaceBase(object):
    """The abstract base class for interfaces. Inherited classes must 
    implement the abstract methods."""
    def __init__(self):
        self._is_running = threading.Event()
        self._recv_string_rest = ""

    def stop(self):
        self._is_running.clear()

    def _parselines(self, recv_data):
        """Returns a list of lines with line end characters. ``None`` if the 
        recv_data is an empty string. An empty list is return if no newline 
        character was received.
        
        Todo: This function is quite a plague to implement. Need to find out 
        better methods...
        """
        if not recv_data:
            # Remote host closed the connection when an empty string is 
            # received. In that case, the rest string buffer is cleared.
            self._recv_string_rest = ""
            return None
        recv_string_list = list([""])
        recv_string = self._recv_string_rest + recv_data.decode("utf8")
        if "\n" in recv_string:
            # TODO: 
            # - splitlines is also splitting lines for \r and others. 
            # Usuall only \n is should be used as command delimiter.
            recv_string_list = recv_string.splitlines(True)
            last_string = recv_string_list.pop()
            if "\n" in last_string:
                self._recv_string_rest = ""
                recv_string_list.append(last_string)
            else:
                self._recv_string_rest = last_string
        else:
            self._recv_string_rest = recv_string
        return recv_string_list

    @abc.abstractmethod
    def write(self, data):
        bytes_written = 0
        return bytes_written

    @abc.abstractmethod
    def data_handler(self, recv_queue):
        while self._is_running.is_set():
            time.sleep(1)


class SCPIInterfaceTCP(SCPIInterfaceBase):
    SELECT_TIMEOUT = 1
    BUFFER_SIZE = 1024

    def __init__(self, *args, **kwargs):
        """Instantiates a TCP interface and binds to the socket. Exceptions 
        must be handled by the instance holder."""
        SCPIInterfaceBase.__init__(self)

        # Check parameter.
        if "ip" in kwargs:
            local_host = kwargs["ip"]
        else:
            local_host = utils.get_local_ip(default_ip="")
        if "port" in kwargs:
            port = kwargs["port"]
        else:
            port = 5025

        # Initialize member variables.
        self._addr = (local_host, port)
        self._socket_remote = None
        self._remote_addr = None
        self._recv_string_rest = ""

        # Bind to TCP socket. Exceptions must be handled by instance holder.
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setblocking(0)
        self._socket.bind(self._addr)
        logging.info("TCP socket bound to {}. Waiting for client connection"
            .format(self._addr))

    def __str__(self):
        return "TCP Interface {}".format(self._addr)

    def write(self, data):
        bytes_written = None
        if self._socket_remote:
            bytes_written = self._socket_remote.send(data.encode("utf8"))
        return bytes_written

    def data_handler(self, recv_queue):
        """The ``data_handler()`` function will handle the connections to the 
        clients, receive data and fill the ``recv_queue`` with received 
        commands. It will run until ``stop()`` is called.
        
        TODO: Currently, I commented the exception handler out. This is 
        because I want some errors during development to pop up. For 
        production code, the data_handler should be self-sustaining.
        """
        inputs = [self._socket]
        self._socket.listen(1)
        
        self._is_running.set()
        while self._is_running.is_set() and inputs:
            # A timeout must be set to be able to catch the stop() event.
            readables, writeables, exceptionals = select.select(
                inputs, [], inputs, SCPIInterfaceTCP.SELECT_TIMEOUT)

            for readable in readables:
                if readable is self._socket:
                    # The server is able to accept connections.
                    if self._socket_remote is None:
                        self._socket_remote, self._remote_addr = \
                            readable.accept()
                        self._socket_remote.setblocking(0)
                        inputs.append(self._socket_remote)
                        logging.info("TCP client connection established: {}"
                            .format(self._remote_addr))
                else:
                    # The client has sent data.
                    recv_data = readable.recv(SCPIInterfaceTCP.BUFFER_SIZE)
                    logging.debug("TCP received data: {!r}".format(recv_data))
                    recv_data_list = self._parselines(recv_data)
                    if recv_data_list is None:
                        # Received empty string => Connection closed by 
                        # client.
                        inputs.remove(readable)
                        readable.close()
                        if readable is self._socket_remote:
                            self._socket_remote = None
                            self._remote_addr = None
                        logging.info("TCP connection closed by client.")
                    else:
                        # Received ordinary data. Parse lines and put into the 
                        # receive queue.
                        for recv_string in recv_data_list:
                            if recv_string:
                                data = (self, recv_string)
                                recv_queue.put(data)

            for exceptional in exceptionals:
                logging.warning("TCP Handler: Got one exceptional: {}"
                    .format(exceptional))
                self._inputs.remove(exceptional)
                exceptional.close()
        
        # Close all open sockets.
        for s in inputs:
            try:
                s.shutdown(socket.SHUT_RDWR)
            except:
                pass
            s.close()
        logging.info("TCP handler has stopped. {}".format(self._addr))


class SCPIInterfaceUDP(SCPIInterfaceBase):
    SELECT_TIMEOUT = 1
    BUFFER_SIZE = 1024

    def __init__(self, *args, **kwargs):
        SCPIInterfaceBase.__init__(self)

        # Check input variables.
        if "ip" in kwargs:
            local_host = kwargs["ip"]
        else:
            local_host = utils.get_local_ip()
        if "port" in kwargs:
            port = kwargs["port"]
        else:
            port = 5025
        
        # Initialize member variables.
        self._addr = (local_host, port)
        self._addr_target = None,

        # Bind server socket.
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setblocking(0)
        self._socket.bind(self._addr)
        logging.info("UDP socket bound to {}.".format(self._addr))

    def __str__(self):
        return "UDP Interface {}".format(self._addr)

    def write(self, data):
        """Data will be sent to the host which most recently sent data to 
        this interface."""
        bytes_written = 0
        if self._addr_target is not None:
            data = data.encode("utf8")
            bytes_written = self._socket.sendto(data, self._addr_target)
        return bytes_written

    def data_handler(self, recv_queue):
        inputs = [self._socket]

        self._is_running.set()
        while self._is_running.is_set() and inputs:
            readables, _, _ = select.select(
                inputs, [], inputs, SCPIInterfaceUDP.SELECT_TIMEOUT)

            for readable in readables:
                recv_data, self._addr_target = readable.recvfrom(
                    SCPIInterfaceUDP.BUFFER_SIZE)
                logging.debug("UDP received data from {}: {!r}".format(
                    self._addr_target, recv_data))
                recv_string_list = self._parselines(recv_data)
                if recv_string_list is not None:
                    for recv_string in recv_string_list:
                        data = (self, recv_string)
                        recv_queue.put(data)
        self._socket.close()
        logging.info("UDP handler has stopped. {}".format(self._addr))

class SCPIInterfaceSerial(SCPIInterfaceBase):
    def __init__(self, *args, **kwargs):
        SCPIInterfaceBase.__init__(self)

        if not HAS_SERIAL:
            warnings.warn("A serial interface was instantiated, but the "
                "package pyserial is not installed. Attemps in establishing a "
                "serial communication will result in wild Exceptions.")
            raise NotImplementedError("No pyserial package available")
        raise NotImplementedError("Not yet implemented")

    def __str__(self):
        return "Serial"

    def write(self, data):
        raise NotImplementedError

    def data_handler(self, recv_queue):
        self._is_running.set()
        while self._is_running.is_set():
            time.sleep(1)
