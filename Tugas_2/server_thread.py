from socket import *
import socket
import threading
import logging
import datetime

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        try:
            while True:
                data = self.connection.recv(32)  
                if not data:
                    break

                msg = data.decode('utf-8')
                logging.warning(f"[SERVER] Received: {msg.strip()}")
                
                if msg == "TIME\r\n":
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    response = f"JAM {now}\r\n"
                    self.connection.sendall(response.encode('utf-8'))
                    logging.warning(f"[SERVER] Sent: {response.strip()}")
                
                elif msg == "QUIT\r\n":
                    logging.warning(f"[SERVER] Received QUIT from {self.address}")
                    break
        except Exception as e:
            logging.error(f"[ERROR] {e}")
        finally:
            self.connection.close()
            logging.warning(f"[SERVER] Connection closed for {self.address}")

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', 45000))
        self.my_socket.listen(5)
        logging.warning("Server listening on port 45000...")
        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"Connection from {client_address}")
            clt = ProcessTheClient(connection, client_address)
            clt.start()
            self.the_clients.append(clt)

def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(message)s')
    svr = Server()
    svr.start()

if __name__ == "__main__":
    main()
