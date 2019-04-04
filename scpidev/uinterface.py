try:
    import socket
    import time
    import logging
except ImportError:
    from . import logging_mockup as logging
    import utime as time
    import usocket as socket


class SCPIInterfaceBase(object):
    """The abstract base class for interfaces. Inherited classes must
    implement the abstract methods."""
    def __init__(self):
        self._recv_string_rest = ""

    def stop(self):
        raise NotImplementedError("Stop not implemented")

    def _parselines(self, recv_data):
        """Returns a list of lines with line end characters. ``None`` if the
        recv_data is an empty string. An empty list is return if no newline
        character was received.

        TODO: This function is quite a plague to implement. Need to find out
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

    def write(self, data):
        raise NotImplementedError("write not implemented")

    def data_handler(self, recv_queue):
        raise NotImplementedError("data_handler not implemented")


class SCPIInterfaceTCP(SCPIInterfaceBase):
    RECV_TIMEOUT = 1
    BUFFER_SIZE = 1024

    def __init__(self, *args, **kwargs):
        """Instantiates a TCP interface and binds to the socket. Exceptions
        must be handled by the instance holder."""
        SCPIInterfaceBase.__init__(self)

        # Check parameter.
        if "ip" in kwargs:
            local_host = kwargs["ip"]
        else:
            local_host = "0.0.0.0"
        if "port" in kwargs:
            port = kwargs["port"]
        else:
            port = 5025

        # Initialize member variables.
        self._addr = None
        self._socket_remote = None
        self._remote_addr = None
        self._recv_string_rest = ""

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        addr = socket.getaddrinfo(local_host, port)[0][-1]
        self._socket.bind(addr)
        logging.info("TCP socket bound to {}. Waiting for client connection"
            .format(self._addr))

    def __str__(self):
        return "TCP Interface {}".format(self._addr)

    def write(self, data):
        bytes_written = None
        if self._socket_remote:
            bytes_written = self._socket_remote.send(data.encode("utf8"))
        return bytes_written

    def recv(self):
        self._socket.listen(1)
        self._socket_remote, addr = self._socket.accept()
        print('Connection address: {}'.format(addr))
        data = self._socket_remote.recv(SCPIInterfaceTCP.BUFFER_SIZE)
        if data:
            data = self._parselines(data)
            print('Received data: {}'.format(data))
        return data

    def close(self):
        self._socket_remote.close()
        print("Connection closed.")


class SCPIInterfaceUDP(object):
    def __init__(self):
        raise NotImplementedError("UDP interface not implemented")


class SCPIInterfaceSerial(object):
    def __init__(self):
        raise NotImplementedError("Serial interface not implemented")


def main_test():
    print("main test {}".format(__file__))
    tcp = SCPIInterfaceTCP()
    tcp.recv()
    tcp.close()


if __name__ == "__main__":
    main_test()
