from socket import *
import socket
import logging
from concurrent.futures import ProcessPoolExecutor
from file_protocol import FileProtocol
import multiprocessing
import os

class ClientHandler:
    def __init__(self):
        self.fp = FileProtocol()
    
    def handle_client(self, connection, address):
        try:
            data_received = ""
            while True:
                data = connection.recv(65536) # 64 Kb buffer
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break

            message = data_received.split("\r\n\r\n")[0]
            hasil = self.fp.proses_string(message)
            connection.sendall((hasil + "\r\n\r\n").encode())
        except Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            connection.close()

def run_server(max_workers):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 5000))
    sock.listen(100)
    logging.warning(f"ProcessPoolServer running with {max_workers} workers")
    
    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        try:
            while True:
                conn, addr = sock.accept()
                handler = ClientHandler()
                pool.submit(handler.handle_client, conn, addr)
        except KeyboardInterrupt:
            sock.close()

if __name__ == "__main__":
    os.chdir('files/')
    run_server(max_workers=50)