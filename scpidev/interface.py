import logging
import socket
import time
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
    """The base class for interfaces. Inherited classes must to implement the 
    following methods:
    
    def write(self, data):
        return bytes_written

    def data_handler(self, recv_queue):
        return

    def close(self):
        return
    """
    def __init__(self):
        self._is_running = False

    def stop(self):
        self._is_running = False
        self.close()


class SCPIInterfaceTCP(socket.socket, SCPIInterfaceBase):
    def __init__(self, *args, **kwargs):
        super(SCPIInterfaceTCP, self).__init__(
            socket.AF_INET, socket.SOCK_STREAM)
        if "ip" in kwargs:
            local_host = kwargs["ip"]
        else:
            local_host = utils.get_local_ip()
        if "port" in kwargs:
            port = kwargs["port"]
        else:
            port = 5025
        self._addr = (local_host, port)

    def open(self):
        super(SCPIInterfaceTCP, self).__init__(
            socket.AF_INET, socket.SOCK_STREAM)
        self.bind(self._addr)
        self.listen(1)
        logging.info("TCP socket bound to {}.".format(self._addr))
        logging.info("TCP socket wating for connection...")
        self._new_socket, self._remote_addr = self.accept()
        self._file = self._new_socket.makefile(mode="rw")
        logging.info("TCP socket connection established: {}"
            .format(self._remote_addr))
    
    def write(self, data):
        bytes_written = self._file.write(data)
        self._file.flush()
        return bytes_written

    def data_handler(self, recv_queue):
        self._is_running = True
        while self._is_running:
            try:
                self.open()
            except Exception as e:
                logging.warning(
                    "Could not open TCP interface {}. Exception: {}. Try "
                    "again...".format(str(self), str(e)))
                time.sleep(1)
                continue
            try:
                while self._is_running:
                    data_recv = self._file.readline().strip()
                    if not data_recv:
                        logging.debug("TCP connection closed by client.")
                        break
                    logging.debug("TCP received data: {}".format(
                        repr(data_recv)))
                    # self.write(data_recv)
                    data = (self, data_recv)
                    recv_queue.put(data)
                self.close()
            except Exception as e:
                logging.warning(
                    "Could not Receive data on interface {}. Exception: {}"
                    .format(self, str(e)))
            time.sleep(1)
        logging.info("TCP handler stopped. {}".format(self._addr))


class SCPIInterfaceUDP(socket.socket, SCPIInterfaceBase):
    def __init__(self, *args, **kwargs):
        if "ip" in kwargs:
            local_host = kwargs["ip"]
        else:
            local_host = utils.get_local_ip()
        if "port" in kwargs:
            port = kwargs["port"]
        else:
            port = 5025
        self._addr = (local_host, port)
        self._addr_target = None

    def write(self, data):
        """Data will be sent to the host which most recently sent data to 
        this interface."""
        if type(data) == type(u""):
            data = data.encode("utf8")
        if self._addr_target is not None:
            self.sendto(data, self._addr_target)

    def open(self):
        super(SCPIInterfaceUDP, self).__init__(
            socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(self._addr)
        logging.info("UDP socket bound to {}.".format(self._addr))

    def data_handler(self, recv_queue):
        self._is_running = True
        while self._is_running:
            try:
                self.open()
            except Exception as e:
                logging.info("Could not open UDP interface {}. Exception: {}. "
                    "Try again...".format(str(self._addr), str(e)))
                time.sleep(1)
                continue
            while self._is_running:
                try:
                    (data_recv, self._addr_target) = self.recvfrom(1024)
                except:
                    break
                data_recv = data_recv.decode("utf8").strip()
                data_recv_list = data_recv.split("\n")
                for data_recv in data_recv_list:
                    if data_recv:
                        data = (self, data_recv)
                        recv_queue.put(data)
                        logging.debug("UDP received data from {}: {}".format(
                            repr(self._addr_target), repr(data_recv)))
        logging.info("UDP handler stopped. {}".format(self._addr))

if HAS_SERIAL:
    class SCPIInterfaceSerial(serial.Serial, SCPIInterfaceBase):
        def data_handler(self, recv_queue):
            while True:
                time.sleep(1)
else:
    class SCPIInterfaceSerial(SCPIInterfaceBase):
        def __init__(self, *args, **kwargs):
            logging.error("An serial interface was instantiated, but the "
                "package pyserial is not installed. Attemps in establishing "
                "serial communication will result in wild Exceptions.")

        def data_handler(self, recv_queue):
            self._is_running = True
            while self._is_running:
                time.sleep(1)
