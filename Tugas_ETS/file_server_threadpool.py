from socket import *
import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from file_protocol import FileProtocol
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

def run_threadpool_server(max_workers):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', 5000))
    sock.listen(100)
    logging.warning(f"ThreadPoolServer running with {max_workers} workers")
    
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        try:
            while True:
                conn, addr = sock.accept()
                logging.warning(f"New connection from {addr}")
                handler = ClientHandler()
                pool.submit(handler.handle_client, conn, addr)
        except KeyboardInterrupt:
            logging.warning("Shutting down server...")
        finally:
            sock.close()

if __name__ == "__main__":
    os.chdir('files/')
    run_threadpool_server(max_workers=50)