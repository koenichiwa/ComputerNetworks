import socket
import threading

LOCAL_IP = "localhost"
LOCAL_PORT = 4242

clients = {}


class ClientThread(threading.Thread):
    def __init__(self, conn, addr):
        super().__init__()
        self.username = None
        self.addr = addr
        self.conn = conn

    def handle_new_user(self, data):
        if not data.startswith("HELLO-FROM"):
            conn.sendall("BAD-RQST-HDR\n".encode("utf-8"))
            return False

        parts = data.split()
        if len(parts) != 2:
            conn.sendall("BAD-RQST-BODY\n".encode("utf-8"))
            return False

        name = data.split()[1]
        if len(clients) > 64:
            conn.sendall("BUSY\n".encode("utf-8"))
            return False

        if name in clients:
            conn.sendall("IN-USE\n".encode("utf-8"))
            return False

        self.username = name
        clients[name] = conn
        conn.sendall(f"HELLO {name}\n".encode("utf-8"))

        return True

    def run(self) -> None:
        while True:
            data = self.conn.recv(2048).decode("utf-8")
            if not data:
                break

            if self.username is None:
                if not self.handle_new_user(data):
                    break
            else:
                if data.startswith("SEND"):
                    split_data = data.split()
                    recipient = split_data[1]
                    message = ' '.join(split_data[2:])
                    if recipient not in clients:
                        conn.sendall(f"UNKNOWN\n".encode("utf-8"))
                    else:
                        clients[recipient].sendall(f"DELIVERY {self.username} {message}\n".encode("utf-8"))
                        conn.sendall(f"SEND-OK\n".encode("utf-8"))

                elif data.startswith("WHO"):
                    client_list = ", ".join(list(clients.keys()))
                    conn.sendall(f"WHO-OK {clients}\n".encode("utf-8"))
                else:
                    conn.sendall("BAD-RQST-HDR\n".encode("utf-8"))
                    break
        if self.username is not None:
            del clients[self.username]
        conn.close()


if __name__ == '__main__':
    threads = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((LOCAL_IP, LOCAL_PORT))
        sock.listen()
        while True:
            conn, addr = sock.accept()
            thread = ClientThread(conn, addr)
            threads.append(thread)
            thread.start()
