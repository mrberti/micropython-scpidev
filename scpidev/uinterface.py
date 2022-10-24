"""
A simple single-threaded implementation of interfaces to be used on
MicroPython devices.

TODO:
- Measure and optimize memory footprint
"""
import gc
try:
    import socket
    import select
    import errno
except ImportError:
    import usocket as socket
    import uselect as select
    import uerrno as errno


BUFFER_SIZE_DEFAULT = 128
TIMEOUT_DEFAULT = None

class SCPIInterfaceTCP(object):
    def __init__(self, *args, **kwargs):
        """Initialize the TCP interface. The local socket will be
        created and bound. After initialization, the socket will listen
        for new connections.

        Possible parameters for initialization:
        ``ip``: The ip to where the local socket should be bound
        ``port``: The TCP port
        ``buffer_size``: The default buffer size for receiving data
        ``timeout``: The default timeout time in seconds
        """
        # Initialize member variables to default values
        self.host = "0.0.0.0"
        self.port = 5025
        self._buffer_size = BUFFER_SIZE_DEFAULT
        self._timeout = TIMEOUT_DEFAULT
        self._sock_remote = None
        self._sock_local = None
        # Set parameters from ``kwargs``
        if "ip" in kwargs:
            self.host = kwargs["ip"]
        if "port" in kwargs:
            self.port = kwargs["port"]
        if "buffer_size" in kwargs:
            self._buffer_size = kwargs["buffer_size"]
            print("Buffer size set to: {}".format(self._buffer_size))
        if "timeout" in kwargs:
            self._timeout = kwargs["timeout"]
            print("Default timeout set to: {}".format(self._timeout))
        # Create the socket object
        addr_local = socket.getaddrinfo(self.host, self.port)[0][-1]
        self._sock_local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_local.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Waiting for new connections should not time-out
        self._sock_local.settimeout(None)
        # Bind and listen
        self._sock_local.bind(addr_local)
        self._sock_local.listen(1)

    def write(self, data):
        """Write ``data`` to the remote client. ``data`` must be an
        encodable ``String``. Return the amount of bytes written."""
        bytes_written = None
        if self._sock_remote:
            bytes_written = self._sock_remote.send(data.encode("utf8"))
        print("Bytes written: {}".format(bytes_written))
        return bytes_written

    def recv(self, buffer_size=None, timeout=-1):
        """Receive data as a decoded ``String``."""
        if buffer_size is None:
            buffer_size = self._buffer_size
        if timeout < 0:
            timeout = self._timeout
        data_raw = None
        if not self._sock_remote:
            print("Waiting for new connection...")
            self._sock_remote, addr = self._sock_local.accept()
            self._sock_remote.settimeout(timeout)
            print("New connection: {}".format(addr))
        try:
            data_raw = self._sock_remote.recv(buffer_size)
        except OSError as e:
            if e.value==errno.ETIMEDOUT:
                print("recv timeout after {} seconds.".format(timeout))
            else:
                self.close_remote()
            return None
        if data_raw:
            print("New data: {!r}".format(data_raw))
            return data_raw.decode("utf-8")
        return None

    def recv_poll(self, buffer_size, timeout):
        """Receive data from a socket object and return it. Implemented
        using ``select.poll()``. Not available on Python for Windows.

        TODO:
        - implement correctly and test
        """
        data_raw = None
        # poller = select.poll()
        print("Waiting for new connection (Poll)...")
        self._sock_remote, addr = self._sock_local.accept()
        print("New connection: {}".format(addr))
        data_raw = self._sock_remote.recv(buffer_size)
        # while not data_raw:
        # poller.register(self._sock_remote, select.POLLIN)
        # readables = poller.poll(timeout)
        # print("Poll done!")
        # for readable in readables:
            # print("Readable: {}".format(readable))
            # data_raw = readable[0].recv(buffer_size)
        return data_raw

    def recv_select(self, buffer_size, timeout):
        """Receive data from a socket object and return it. Implemented
        using ``select.select()``. Not available on Unix MicroPython
        port.

        TODO:
        - implement correctly and test"""
        data_raw = None
        inputs = [self._sock_local]
        # while not data_raw:
        readables, _, _ = select.select(inputs,
            [], [], timeout)
        for readable in readables:
            if readable is self._sock_local:
                print("Waiting for new connection...")
                self._sock_remote, self._remote_addr = \
                    readable.accept()
                self._sock_remote.setblocking(0)
                inputs.append(self._sock_remote)
                print("TCP client connection established: {}"
                    .format(self._remote_addr))
            else:
                data_raw = self._sock_remote.recv(buffer_size)
        return data_raw

    def close_remote(self):
        """Close the remote connection."""
        if self._sock_remote:
            print("Closing remote...")
            self._sock_remote.close()
            self._sock_remote = None
            gc.collect()

    def close_local(self):
        """Close the local connection."""
        if self._sock_local:
            print("Closing local socket...")
            self._sock_local.close()
            self._sock_local = None
            gc.collect()

    def close(self):
        """Close the local and remote connections."""
        self.close_remote()
        self.close_local()


def main_test():
    print("main test {}".format(__file__))
    tcp = SCPIInterfaceTCP()
    tcp.recv()
    tcp.close()


if __name__ == "__main__":
    main_test()
