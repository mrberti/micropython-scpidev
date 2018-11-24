#!/usr/bin/env python
import socket
import time
import argparse
import threading

# Create option parser
parser = argparse.ArgumentParser(
    description="Send a message via TCP. A second thread will read the data "
    "from the connection.")
parser.add_argument("ip", metavar="REMOTEHOST", type=str, help="The IP address of the instrument")
parser.add_argument("port", metavar="PORT", type=int, help="The TCP port.")
parser.add_argument("msg", metavar="MESSAGE", type=str, help="The message to be sent, e.g. "
    "'MEAS?'. Attention: When invoking from Bash, you should use $'MEAS\\n' to "
    "correctly send the new line character (single quotes matter).")
parser.add_argument("-N", type=int, help="Repets the sending of the meassage "
    "N-times. If N=0 the message is sent indefinitely.", default=1)
parser.add_argument("-d", type=float, help="Delay in seconds between "
    "messages. Default: 1s", default=1.)
parser.add_argument("--udp", help="Use UDP connection instead of TCP. When "
    "the server is bound to the same local IP, receiving is not possible", 
    action="store_true")

# Get options
args = parser.parse_args()
N = args.N
repeat_indefinitely = (N == 0)
interval = args.d
port = args.port
remote_ip = args.ip
addr = (remote_ip, port)
msg = args.msg
use_udp = args.udp

# Get outbound IP
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("1.1.1.1", 80))
    local_ip = sock.getsockname()[0]
except Exception as e:
    local_ip = "localhost"
sock.close()
addr_local = (local_ip, port)

# Create socket and connect
if use_udp:
    print("Using UDP.")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
else:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(addr)
    except ConnectionRefusedError:
        print("Connection refused by {}. Is the server running?".format(addr))
        exit()
    print("Connected to {}".format(str(sock)))

# Create and start the reader thread
def read_data(event):
    """Target function for reader thread."""
    try:
        sock.bind(addr_local)
    except Exception as e:
        print("Can't bind to {}. Reading not possible. Exception: {}"
            .format(str(addr), str(e)))
        return
    while True:
        data = sock.recv(1024)
        if not data:
            break
        print("< {}".format(repr(data)))
    print("Connection closed by server.")
    event.set()
event = threading.Event()
t = threading.Thread(target=read_data, name="Read data", args=(event,))
t.daemon = True
t.start()

# Send out message
try:
    while (N or repeat_indefinitely) and not event.is_set():
        data = msg.encode("utf8")
        if use_udp:
            sent = sock.sendto(data, addr)
        else:
            sent = sock.send(data)
        print("> {}".format(repr(data)))
        if not repeat_indefinitely:
            N -= 1
        time.sleep(interval)
except KeyboardInterrupt:
    pass

# Clean up
sock.close()
