import signal
import socket
from ble_client import DualStimClient
from time import sleep

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

HOST = '0.0.0.0'
PORT = 8887


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("Awaiting client connection...")

s.bind((HOST, PORT))
s.listen()
conn, addr = s.accept()

print("Set up TCP Server, connected to VST Client.")

""
print("\nSetting up StimClient object")

stimclient = DualStimClient()
stimclient.connect()



def do_with_data(d):
    print("Sending 'flip' instruction to StimClient()")

while True:
    data = conn.recv(10)
    if not data:
        break
    print(data)
    match data.decode('utf-8').split('\n')[0]:
        case 's':
            stimclient.pos_1()
        case 'd':
            stimclient.off_1()
        case 'f':
            stimclient.neg_1()
        case 'j':
            stimclient.pos_2()
        case 'k':
            stimclient.off_2()
        case 'l':
            stimclient.neg_2()
        case 'o':
            stimclient.off()
        case 'b':
            stimclient.seizure()
        

