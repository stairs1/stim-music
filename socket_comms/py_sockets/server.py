#!/usr/bin/env python3
import signal
import socket

shut_up = False

def handler(wenis, wenis_2):
    shut_up = True

# signal.signal(signal.SIGINT, handler)

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 8889        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print('Connected by', addr)
        while not shut_up:
            data = conn.recv(2)
            if not data:
                break
            print(data)



print("Bruh moment")


