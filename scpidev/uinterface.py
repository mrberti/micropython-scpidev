import gc
try:
    import socket
except ImportError:
    import usocket as socket


BUFFER_SIZE_DEFAULT = 128
TIMEOUT_DEFAULT = 5

class SCPIInterfaceTCP(object):
    def __init__(self, *args, **kwargs):
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
        bytes_written = None
        if self._sock_remote:
            bytes_written = self._sock_remote.send(data.encode("utf8"))
        return bytes_written

    def recv(self, buffer_size=None, timeout=None):
        if buffer_size is None:
            buffer_size = self._buffer_size
        if timeout is None:
            timeout = self._timeout
        self.close()
        self._sock_local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_local.settimeout(timeout)
        addr_local = socket.getaddrinfo(self.host, self.port)[0][-1]
        self._sock_local.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self._sock_local.bind(addr_local)
        
        self._sock_local.listen(1)
        try:
            self._sock_remote, addr = self._sock_local.accept()
            print("New connection: {}".format(addr))
        except OSError as exc:
            # Micropython does not implement ``socket.timeout``
            print("Error on accept. {}".format(exc))
            return None
        data_raw = self._sock_remote.recv(buffer_size)
        if data_raw:
            print("New data: {!r}".format(data_raw))
            return data_raw.decode("utf-8")
        return None

    def close_remote(self):
        if self._sock_remote:
            print("Closing remote...")
            self._sock_remote.close()

    def close(self):
        if self._sock_local:
            self._sock_local.close()
        if self._sock_remote:
            self._sock_remote.close()
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
