import socket
import threading
from queue import Queue

class Client:

    HOST = '84.229.236.192'
    PORT = 50001

    def __init__(self, event):
        self.connected = True
        self.accept_queue = Queue()
        self.connected_event = event
        self.sent_data = threading.Event()

    def handle_close(self):
        self.soc.close()

    def send_data(self, data):
        data = str(data).encode('utf-8')
        self.soc.sendall(data)
        return True

    def accept_data(self):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.connect((self.HOST, self.PORT))
        self.connected_event.set()
        while True:
            try:
                data = self.soc.recv(1012)
            except:
                return
            self.accept_queue.put(data.decode('utf-8'))

        self.soc.close()




if __name__ == "__main__":
    Client()
