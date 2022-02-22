import signal
import socket
from ble_client import *

s = None
conn = None

def handler(*args):
    print("Received shutdown request...")
    if s is not None:
        conn.shutdown(socket.SHUT_RDWR)
        s.close()
    sleep(1000)
    print("Closed socket, exiting now")
    exit(0)

signal.signal(signal.SIGINT, handler)

HOST = '127.0.0.1'
PORT = 8889


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("Awaiting client connection...")

s.bind((HOST, PORT))
s.listen()
conn, addr = s.accept()

print("Set up TCP Server, connected to VST Client.")

"""
print("\nSetting up StimClient object")

stimclient = StimClient()
"""


def do_with_data(d):
    print("Sending 'flip' instruction to StimClient()")

while True:
    data = conn.recv(10)
    if not data:
        break
    print(data)
    # Call the flip command.

