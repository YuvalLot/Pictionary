
import socket
import threading


class Server:

    HOST = "localhost"
    PORT = 400

    def __init__(self):
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soc.bind((self.HOST, self.PORT))
        self.cons = []
        self.addrs = []
        self.addr_index = 0
        self.accept_connection()

    def accept_connection(self):
        self.soc.listen()
        conn, addr = self.soc.accept()
        self.cons.append(conn)
        self.addrs.append(addr)
        threading.Thread(target=self.accept_input, args=(len(self.cons)-1,)).start()
        if len(self.cons) == 1:
            print("hello")
            self.cons[0].sendall(b'your turn ')
        self.accept_connection()

    def accept_input(self, con_index):
        with self.cons[con_index]:
            print(f"Connected by {self.addrs[con_index]}")
            print(self.cons[con_index])
            while self.cons[con_index]:
                try:
                    data = self.cons[con_index].recv(1012)
                except ConnectionResetError:
                    break
                except OSError:
                    print(self.cons[con_index])
                if not data:
                    break
                if data == b'done':
                    self.addr_index = (self.addr_index + 1) % len(self.addrs)
                    while not self.cons[self.addr_index]:
                        self.addr_index = (self.addr_index + 1) % len(self.addrs)
                    self.cons[self.addr_index].sendall(b'your turn ')
                for i, con in enumerate(self.cons):
                    if con and i != con_index:
                        con.sendall(data)

        self.cons[con_index] = None
        self.addrs[con_index] = None


if __name__ == "__main__":
    Server()
