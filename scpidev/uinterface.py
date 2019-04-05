import gc
try:
    import socket
except ImportError:
    import usocket as socket


class SCPIInterfaceTCP(object):
    RECV_TIMEOUT = 3
    BUFFER_SIZE = 128

    def __init__(self, *args, **kwargs):
        if "ip" in kwargs:
            self.host = kwargs["ip"]
        else:
            self.host = "0.0.0.0"
        if "port" in kwargs:
            self.port = kwargs["port"]
        else:
            self.port = 5025
        self._sock_local = None
        self._sock_remote = None

    def write(self, data):
        bytes_written = None
        if self._sock_remote:
            bytes_written = self._sock_remote.send(data.encode("utf8"))
        return bytes_written

    def recv(self):
        self.close()
        self._sock_local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_local.settimeout(self.RECV_TIMEOUT)
        addr = socket.getaddrinfo(self.host, self.port)[0][-1]
        try:
            self._sock_local.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock_local.bind(addr)
        except Exception as exc:
            print("EXCEPTION: {}".format(exc))
        self._sock_local.listen(1)
        try:
            self._sock_remote, addr = self._sock_local.accept()
        except OSError:
            self.close()
            return None
        data_raw = self._sock_remote.recv(SCPIInterfaceTCP.BUFFER_SIZE)
        if data_raw:
            try:
                return data_raw.decode("utf-8")
            except Exception as exc:
                print("ERROR {}".format(exc))
        return None

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
