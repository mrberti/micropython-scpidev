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
    logging.warning("Could not load ``serial`` package. The serial "
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
        self.close()

    @abc.abstractmethod
    def write(self, data):
        pass

    @abc.abstractmethod
    def data_handler(self, recv_queue):
        pass

    @abc.abstractmethod
    def close(self):
        pass


class SCPIInterfaceTCP(SCPIInterfaceBase):
    def __init__(self, *args, **kwargs):
        SCPIInterfaceBase.__init__(self)

        # Check arguements.
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
        self._recv_string_rest = ""

        # Bind to TCP socket.
        try:
            self._socket.bind(self._addr)
            self._socket.listen(1)
        except Exception as e:
            logging.warning("Could not open TCP interface {}. Exception: {}. "
                .format(str(self._addr), str(e)))
            raise e
        logging.info("TCP socket bound to {}.".format(self._addr))
        logging.info("TCP socket waiting for connection...")

    def __str__(self):
        return "TCP {}".format(self._addr)

    def open(self):
        self._socket_remote, self._remote_addr = self._socket.accept()
        logging.info("TCP socket connection established: {}"
            .format(self._remote_addr))

    def close(self):
        self._close_remote()
        try:
            self._socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self._socket.close()

    def _close_remote(self):
        try:
            self._socket_remote.close()
        except:
            pass
    
    def write(self, data):
        bytes_written = self._socket_remote.send(data.encode("utf8"))
        return bytes_written

    def read_data(self):
        return self._socket_remote.recv(1024)

    def _readlines(self):
        """Returns a list of lines with line end characters. This function is 
        necessary, becase when using socket.makefile, the readline is blocking 
        the thread.
        
        Todo: This function is quite a plague to implement. Need to find out 
        better methods...
        """
        while True:
            recv_data = self._socket.read_data()
            if not recv_data:
                # Remote host closed the connection when an empty string is 
                # received. In that case, the rest string buffer is cleared.
                self._recv_string_rest = ""
                return list([""])
            logging.debug("TCP received data: {}".format(repr(recv_data)))
            recv_string = self._recv_string_rest + recv_data.decode("utf8")
            logging.debug("Buffer: {}".format(repr(recv_string)))
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

    def data_handler(self, recv_queue):
        self._is_running.set()
        while self._is_running.is_set():
            try:
                self.open()
            except Exception as e:
                logging.warning(
                    "Could not open TCP interface {}. Exception: {}. Try "
                    "again...".format(self, e))
                time.sleep(1)
                continue
            try:
                while self._is_running:
                    recv_string_list = self._readlines()
                    if not recv_string_list[0]:
                        logging.debug("TCP connection closed by client.")
                        break
                    for recv_string in recv_string_list:
                        if recv_string:
                            data = (self, recv_string)
                            recv_queue.put(data)
            except Exception as e:
                logging.warning(
                    "Could not Receive data on interface {}. Exception: {}"
                    .format(self, e))
        logging.info("TCP handler stopped. {}".format(self._addr))


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
        try:
            self._socket.bind(self._addr)
        except Exception as e:
            logging.warning("Could not open UDP interface {}. Exception: {}. "
                .format(str(self._addr), str(e)))
            raise e
        logging.info("UDP socket bound to {}.".format(self._addr))

    def __str__(self):
        return "UDP {}".format(self._addr)

    def write(self, data):
        """Data will be sent to the host which most recently sent data to 
        this interface."""
        if type(data) == type(u""):
            data = data.encode("utf8")
        if self._addr_target is not None:
            self._socket.sendto(data, self._addr_target)

    def close(self):
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()

    def _readlines(self):
        """Returns a list of lines with line end characters. This function is 
        necessary, becase when using socket.makefile, the readline is blocking 
        the thread.
        
        Todo: This function is quite a plague to implement. Need to find out 
        better methods...
        """
        while True:
            (recv_data, self._addr_target) = self._socket.recvfrom(1024)
            logging.debug("UDP received data: {}".format(repr(recv_data)))
            recv_string = self._recv_string_rest + recv_data.decode("utf8")
            logging.debug("Buffer: {}".format(repr(recv_string)))
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

    def data_handler(self, recv_queue):
        self._is_running.set()
        while self._is_running.is_set():
            while self._is_running.is_set():
                try:
                    recv_string_list = self._readlines()
                except:
                    break
                for recv_string in recv_string_list:
                    # if recv_string:
                    data = (self, recv_string)
                    recv_queue.put(data)
                    logging.debug("UDP received data from {}: {}".format(
                        repr(self._addr_target), repr(recv_string)))
        logging.info("UDP handler stopped. {}".format(self._addr))

class SCPIInterfaceSerial(SCPIInterfaceBase):
    def __init__(self, *args, **kwargs):
        SCPIInterfaceBase.__init__(self)

        if not HAS_SERIAL:
            logging.error("A serial interface was instantiated, but the "
                "package pyserial is not installed. Attemps in establishing a "
                "serial communication will result in wild Exceptions.")
            return
        pass

    def __str__(self):
        return "Serial"

    def close(self):
        raise NotImplementedError

    def write(self, data):
        raise NotImplementedError

    def data_handler(self, recv_queue):
        self._is_running.set()
        while self._is_running.is_set():
            time.sleep(1)
