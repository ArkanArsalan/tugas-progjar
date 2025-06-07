import sys
import socket
import logging


def send_time_request():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('172.16.16.101', 45000) 
    sock.connect(server_address)
    try:
        message = "TIME\r\n"
        logging.warning(f"[CLIENT] Sending: {message.strip()}")
        sock.sendall(message.encode('utf-8'))

        full_data = b""
        while True:
            data = sock.recv(16)
            if not data:
                break
            full_data += data
            if b'\r\n' in full_data:
                break
        logging.warning(f"[CLIENT] Received: {full_data.decode().strip()}")

        quit_message = "QUIT\r\n"
        sock.sendall(quit_message.encode('utf-8'))
    finally:
        sock.close()


if __name__=='__main__':
    for i in range(1,5):
        send_time_request()
