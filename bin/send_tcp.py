#!/usr/bin/env python
import socket
import time
import argparse
import threading

def read_data(event):
    """Target function for reader thread."""
    while True:
        data = sock.recv(1024)
        if not data:
            break
        print("< {}".format(repr(data)))
    print("Connection closed by server.")
    event.set()

# Create option parser
parser = argparse.ArgumentParser(
    description="Send a message via TCP. A second thread will read the data "
    "from the connection.")
parser.add_argument("ip", type=str, help="The IP address of the instrument")
parser.add_argument("port", type=int, help="The TCP port.")
parser.add_argument("msg", type=str, help="The message to be sent, e.g. "
    "MEAS?")
parser.add_argument("-N", type=int, help="Repets the sending of the meassage "
    "N-times. If N=0 the message is sent indefinitely.", default=1)
parser.add_argument("-d", type=float, help="Delay between messages. Default: "
    "1.0 s", default=1.)

# Get options
args = parser.parse_args()
N = args.N
repeat_indefinitely = (N == 0)
interval = args.d
addr = (args.ip, args.port)
msg = args.msg

# Create socket and connect
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    sock.connect(addr)
except ConnectionRefusedError:
    print("Connection refused by {}. Is the server running?".format(addr))
    exit()

# Create and start the reader thread
event = threading.Event()
t = threading.Thread(target=read_data, name="Read data", args=(event,))
t.daemon = True
t.start()

# Send out message
try:
    while (N or repeat_indefinitely) and not event.is_set():
        sent = sock.send(msg.encode("utf8"))
        print("> Sent bytes: {}".format(sent))
        if not repeat_indefinitely:
            N -= 1
        time.sleep(interval)
except KeyboardInterrupt:
    pass

# Clean up
sock.close()
