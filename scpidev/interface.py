import logging
import socket
import time
import threading
import abc
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

    def stop(self):
        self._is_running.clear()

    @abc.abstractmethod
    def write(self, data):
        pass

    @abc.abstractmethod
    def data_handler(self, recv_queue):
        pass


class SCPIInterfaceTCP(SCPIInterfaceBase):
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
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._addr = (local_host, port)
        self._socket_remote = None
        self._remote_addr = None
        self._recv_string_rest = ""

        # Bind to TCP socket. Exceptions must be handled by instance holder.
        self._socket.bind(self._addr)
        self._socket.listen(1)
        logging.info("TCP socket bound to {}. Waiting for client connection"
            .format(self._addr))

    def __str__(self):
        return "TCP Interface {}".format(self._addr)

    def _open(self):
        self._socket_remote = None
        self._remote_addr = None

        # To make the waiting for connections non-blocking, the timeout is set
        # to a reasonable low value.
        timeout = self._socket.gettimeout()
        self._socket.settimeout(1)
        while self._is_running.is_set():
            try:
                self._socket_remote, self._remote_addr = self._socket.accept()
                break
            except socket.timeout:
                continue
        self._socket.settimeout(timeout)
        if self._is_running.is_set():
            logging.info("TCP client connection established: {}"
                .format(self._remote_addr))

    def _close(self):
        self._close_remote()
        self._socket.close()

    def _close_remote(self):
        if self._socket_remote:
            logging.debug("Closing remote socket {}".format(self._remote_addr))
            try:
                self._socket_remote.shutdown(socket.SHUT_RDWR)
                self._socket_remote.close()
            except Exception as e:
                logging.debug("Could not close remote socket. {}".format(e))
        self._socket_remote = None
        self._remote_addr = None

    def write(self, data):
        bytes_written = self._socket_remote.send(data.encode("utf8"))
        return bytes_written

    def _read_data(self, buffer_size=1024):
        # To make the waiting for connections non-blocking, the timeout is set
        # to a reasonable low value.
        timeout = self._socket.gettimeout()
        self._socket_remote.settimeout(1)
        data = b""
        while self._is_running.is_set():
            try:
                data = self._socket_remote.recv(buffer_size)
                break
            except socket.timeout:
                continue
        self._socket.settimeout(timeout)
        return data

    def _readlines(self):
        """Returns a list of lines with line end characters. This function is 
        necessary, becase when using socket.makefile, the readline is blocking 
        the thread.
        
        Todo: This function is quite a plague to implement. Need to find out 
        better methods...
        """
        # Here we can use an infinite loop, because ``_read_data()`` is 
        # non-blocking. When our client disconnects or the server is shut-down 
        # an empty byte string is received.
        while True:
            recv_data = self._read_data()
            if not recv_data:
                # Remote host closed the connection when an empty string is 
                # received. In that case, the rest string buffer is cleared.
                self._recv_string_rest = ""
                return list([""])
            logging.debug("TCP received data: {!r}".format(recv_data))
            recv_string = self._recv_string_rest + recv_data.decode("utf8")
            logging.debug("TCP receive buffer: {!r}".format(recv_string))
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
                return recv_string_list
            else:
                self._recv_string_rest = recv_string

    def data_handler(self, recv_queue):
        """The ``data_handler()`` function will handle the connections to the 
        clients, receive data and fill the ``recv_queue`` with received 
        commands. It will run until ``stop()`` is called."""
        self._is_running.set()
        while self._is_running.is_set():
            # TODO: Currently, I commented the exception handler out. This is 
            # because I want to see some errors during development pop up.
            # For production code, the data_handler should be self-sustaining.
            # try:
            self._open()
            while self._is_running.is_set():
                recv_string_list = self._readlines()
                if not recv_string_list[0]:
                    if self._is_running.is_set():
                        logging.info("TCP connection closed by client.")
                    break
                for recv_string in recv_string_list:
                    if recv_string:
                        data = (self, recv_string)
                        recv_queue.put(data)
            # except Exception as e:
            #     logging.warning(
            #         "Could not Receive data on interface {}. Exception: {}"
            #         .format(self, e))
            #     self._close_remote()
        self._close()
        logging.info("TCP handler has stopped. {}".format(self._addr))


class SCPIInterfaceUDP(SCPIInterfaceBase):
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
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._recv_string_rest = ""
        self._addr = (local_host, port)
        self._addr_target = None,

        # Bind server socket.
        self._socket.bind(self._addr)
        logging.info("UDP socket bound to {}.".format(self._addr))

    def __str__(self):
        return "UDP Interface {}".format(self._addr)

    def write(self, data):
        """Data will be sent to the host which most recently sent data to 
        this interface."""
        if type(data) == type(u""):
            data = data.encode("utf8")
        if self._addr_target is not None:
            self._socket.sendto(data, self._addr_target)

    def _close(self):
        self._socket.close()

    def _read(self, buffer_size=1024):
        timeout = self._socket.gettimeout()
        self._socket.settimeout(1)
        while self._is_running.is_set():
            try:
                return self._socket.recvfrom(buffer_size)
            except socket.timeout:
                continue
        return (None, None)

    def _readlines(self):
        """Returns a list of lines with line end characters. This function is 
        necessary, becase when using socket.makefile, the readline is blocking 
        the thread.
        
        TODO: This function is quite a plague to implement. Need to find out 
        better methods...
        """
        recv_string_list = list()
        while self._is_running.is_set():
            recv_data, self._addr_target = self._read()
            if recv_data:
                logging.debug("UDP received data: {!r}".format(recv_data))
                recv_string = self._recv_string_rest + recv_data.decode("utf8")
                logging.debug("Buffer: {!r}".format(recv_string))
                if "\n" in recv_string:
                    recv_string_list = recv_string.splitlines(True)
                    last_string = recv_string_list.pop()
                    if "\n" in last_string:
                        self._recv_string_rest = ""
                        recv_string_list.append(last_string)
                    else:
                        self._recv_string_rest = last_string
                    return recv_string_list
                else:
                    self._recv_string_rest = recv_string
        return recv_string_list

    def data_handler(self, recv_queue):
        self._is_running.set()
        while self._is_running.is_set():
            while self._is_running.is_set():
                recv_string_list = self._readlines()
                for recv_string in recv_string_list:
                    data = (self, recv_string)
                    recv_queue.put(data)
                    logging.debug("UDP received data from {!r}: {!r}".format(
                        self._addr_target, recv_string))
        self._close()
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
