from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread, Lock

LOCAL_IP = "localhost"
LOCAL_PORT = 4242

client_dict_lock = Lock()
clients = {}
MAX_CLIENTS = 64


def main():
    threads = []
    with socket(AF_INET, SOCK_STREAM) as sock:
        sock.bind((LOCAL_IP, LOCAL_PORT))
        sock.listen()
        while True:
            conn, addr = sock.accept()
            thread = ClientThread(conn, addr)
            threads.append(thread)
            thread.start()


class ClientThread(Thread):
    def __init__(self, conn, addr):
        super().__init__()
        self.username = None
        self.addr = addr
        self.conn = conn

    def handle_new_user(self, data):
        if not data.startswith("HELLO-FROM"):
            self.conn.sendall("BAD-RQST-HDR\n".encode("utf-8"))
            return False

        parts = data.split()
        if len(parts) != 2:
            self.conn.sendall("BAD-RQST-BODY\n".encode("utf-8"))
            return False

        name = data.split()[1]
        with client_dict_lock:
            if len(clients) >= MAX_CLIENTS:
                self.conn.sendall("BUSY\n".encode("utf-8"))
                return False

            if name in clients:
                self.conn.sendall("IN-USE\n".encode("utf-8"))
                return False

            self.username = name
            clients[name] = self.conn
        self.conn.sendall(f"HELLO {name}\n".encode("utf-8"))
        return True

    def handle_message(self, data):
        if data == "WHO\n":
            with client_dict_lock:
                client_list = ", ".join(list(clients.keys()))
            self.conn.sendall(f"WHO-OK {client_list}\n".encode("utf-8"))
        elif data.startswith("SEND"):
            split_data = data.split()
            if len(data < 3):
                self.conn.sendall("BAD-RQST-BODY\n".encode("utf-8"))
            else:
                recipient = split_data[1]
                message = ' '.join(split_data[2:])
                if recipient not in clients:
                    self.conn.sendall(f"UNKNOWN\n".encode("utf-8"))
                else:
                    with client_dict_lock:
                        clients[recipient].sendall(f"DELIVERY {self.username} {message}\n".encode("utf-8"))
                    self.conn.sendall(f"SEND-OK\n".encode("utf-8"))
        else:
            self.conn.sendall("BAD-RQST-HDR\n".encode("utf-8"))

    def run(self) -> None:
        while True:
            data = self.conn.recv(2048).decode("utf-8")
            if not data:
                break
            if self.username is None:
                if not self.handle_new_user(data):
                    break
            else:
                self.handle_message(data)

        if self.username is not None:
            with client_dict_lock:
                del clients[self.username]
        self.conn.close()


if __name__ == '__main__':
    main()
