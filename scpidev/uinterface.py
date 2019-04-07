import gc
try:
    import socket
    import select
except ImportError:
    import usocket as socket
    import uselect as select


BUFFER_SIZE_DEFAULT = 128
TIMEOUT_DEFAULT = None

class SCPIInterfaceTCP(object):
    def __init__(self, *args, **kwargs):
        """Possible parameters for initialization:
        ``ip``: The ip to where the local socket should be bound
        ``port``: The TCP port
        ``buffer_size``: The default buffer size for receiving data
        ``timeout``: The default timeout time in seconds
        """
        self.host = "0.0.0.0"
        self.port = 5025
        self._buffer_size = BUFFER_SIZE_DEFAULT
        self._timeout = TIMEOUT_DEFAULT
        self._sock_remote = None
        self._sock_local = None

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

    def write(self, data):
        """Write ``data`` to the remote client. ``data`` must be an
        encodable ``String``. Return the amount of bytes written."""
        bytes_written = None
        if self._sock_remote:
            bytes_written = self._sock_remote.send(data.encode("utf8"))
        print("Bytes written: {}".format(bytes_written))
        return bytes_written

    def recv(self, buffer_size=None, timeout=None):
        """Receive data as a decoded ``String``. This implementation
        opens a new connection on every call. The caller should call
        ``close_remote()`` after receiving the data."""
        if buffer_size is None:
            buffer_size = self._buffer_size
        self.close()
        addr_local = socket.getaddrinfo(self.host, self.port)[0][-1]
        self._sock_local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_local.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock_local.settimeout(timeout)
        self._sock_local.bind(addr_local)
        self._sock_local.listen(1)
        if "poll" in dir(select):
            data_raw = self.recv_poll(buffer_size, timeout)
        else:
            # Python on windows does not have a ``poll`` implementation
            data_raw = self.recv_select(buffer_size, timeout)
        print("New data: {!r}".format(data_raw))
        if data_raw:
            return data_raw.decode("utf-8")
        else:
            return None

    def recv_poll(self, buffer_size, timeout):
        """Receive data from a socket object and return it. Implemented
        using ``select.poll()``. Not available on Python for Windows."""
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
        port."""
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

    def close(self):
        """Close the local and remote connections."""
        if self._sock_remote:
            self._sock_remote.close()
        if self._sock_local:
            self._sock_local.close()
        # Hint: It seems, that you cannot re-use sockets on Micropython
        # so it has to be deleted.
        del self._sock_local, self._sock_remote
        gc.collect()
        self._sock_local = self._sock_remote = None


def main_test():
    print("main test {}".format(__file__))
    tcp = SCPIInterfaceTCP()
    tcp.recv()
    tcp.close()


if __name__ == "__main__":
    main_test()
