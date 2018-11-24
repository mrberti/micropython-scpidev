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
except ImportError:
    logging.warning("Could not load ``serial`` package.")


class SCPIInterface():
    def __init__(self, type, *args, **kwargs):
        type = type.lower()
        self._type = type
        self._file = None
        self._serial = None
        self._socket = None
        self._socket_local = None
        self._open_callback = None

        if type == "tcp":
            self._init_tcp(*args, **kwargs)
        elif type == "udp":
            self._init_udp(*args, **kwargs)
        elif type == "serial":
            self._init_serial(*args, **kwargs)
        else:
            raise Exception("Interface type '{}' is not supported.".format(
                str(type)))

    def __str__(self):
        result = "{t}".format(t=self._type)
        if self.is_tcp() or self.is_udp():
            return (result + " " + str(self._addr))
        elif self.is_serial():
            return (result + " (" + str(self._serial.port) + ", " 
                + str(self._serial.baudrate) + ")")
        else:
            raise NotImplementedError("An unsupported type was sepcified: {}"
                .format(self._type))

    def is_tcp(self):
        return (self._type == "tcp")

    def is_udp(self):
        return (self._type == "udp")

    def is_serial(self):
        return (self._type == "serial")

    def _get_local_ip(self, 
            remote_host="1.1.1.1", remote_port=80, default_ip="localhost"):
        """Try to find out the local ip by establishing a test connection to 
        a known remote host."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((remote_host, remote_port))
            ip = sock.getsockname()[0]
        except Exception as e:
            ip = default_ip
            logging.warning("Could not get the local IP. Using default: {}. "
                "Exception: {}".format(ip, str(e)))
        sock.close()
        return ip

    def _init_tcp(self, ip=None, port=5025):
        if ip is None:
            ip = self._get_local_ip()
        self._addr = (ip, port)
        self._open_callback = self._open_tcp

    def _init_udp(self, ip=None, port=5025):
        if ip is None:
            ip = self._get_local_ip()
        self._addr = (ip, port)
        self._open_callback = self._open_udp

    def _init_serial(self, *args, **kwargs):
        self._serial = serial.Serial(*args, **kwargs)
        self._file = self._serial
        self._open_callback = self._open_serial

    def _open_tcp(self):
        self._socket_local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket_local.bind(self._addr)
        self._socket_local.listen(1)
        logging.info("TCP socket bound to {}.".format(self._addr))
        logging.info("TCP socket wating for connection...")
        self._socket, self._remote_addr = self._socket_local.accept()
        self._file = self._socket.makefile("rw")
        logging.info("TCP socket connection established: {}"
            .format(self._remote_addr))

    def _open_udp(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind(self._addr)
        self._file = self._socket.makefile("rw")
        self._remote_addr = None
        logging.info("UDP socket bound to {}.".format(self._addr))

    def _open_serial(self):
        if not self._serial.is_open:
            self._serial.open()
        logging.info("Serial connection open: {}.".format(str(self._serial)))

    def open(self):
        self._open_callback()

    def read(self, size):
        return self._file.read(size)

    def readline(self):
        if self.is_udp():
            result = ""
            while True:
                (data, self._remote_addr) = self._socket.recvfrom(1024)
                data = data.decode("utf8")
                for char in data:
                    if char == "\n":
                        print(repr(char))
                        break
                    result = result + data
            return result
        return self._file.readline()

    def write(self, data):
        if self.is_udp():
            if self._remote_addr is not None:
                self._socket.sendto(data, self._remote_addr)
        bytes_written = self._file.write(data)
        self._file.flush()
        return bytes_written

    def writeline(self, data):
        if not data.endswith("\n"):
            data = data + "\n"
        self.write(data)

    def flush(self):
        raise NotImplementedError
        # self._file.flush()

    def close(self):
        if self._file is not None:
            self._file.close()
        if self._serial is not None:
            self._serial.close()
        if self._socket is not None:
            self._socket.shutdown(socket.SHUT_RDWR)
            self._socket.close()
        if self._socket_local is not None:
            self._socket_local.close()

    def _data_handler_udp(self, data_queue):
        while True:
            try:
                interface.open()
                while True:
                    data = interface.readline()
                    if not data:
                        break
                    print(repr(data))
                    # interface.write(data)
            except KeyboardInterrupt:
                break
            # int_udp.close()
            interface.close()
            logging.info("Connections closed.")
            # int_com.close()
        interface.close()
        logging.info("Server shutdown.")

    def _data_handler_tcp(self, data_queue):
        while True:
            try:
                self.open()
            except Exception as e:
                logging.warning(
                    "Could not open interface {}. Exception: {}"
                    .format(interface, str(e)))
                continue
            try:
                while True:
                    data_recv = self.readline()
                    if not data_recv:
                        break
                    # print(repr(data_recv))
                    data_queue.put(data_recv)
                self.close()
            except Exception as e:
                logging.warning(
                    "Could not Receive data on interface {}. Exception: {}"
                    .format(self, str(e)))
            time.sleep(1)

    def _data_handler_serial(self, data_queue):
        raise NotImplementedError

    def data_handler(self, data_queue):
        if self.is_tcp():
            self._data_handler_tcp(data_queue)
        if self.is_udp():
            self._data_handler_udp(data_queue)
        if self.is_serial():
            self._data_handler_serial(data_queue)
        else:
            raise NotImplementedError

if __name__ == "__main__":
    FORMAT = "<%(levelname)s> %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    int_udp = SCPIInterface("udp")
    int_tcp = SCPIInterface("tcp", ip="localhost")
    int_com = SCPIInterface("serial", port="COM7", baudrate=500000, dsrdtr=1)

    interface = int_tcp
    dq = Queue()
    interface._data_handler_tcp(dq)
