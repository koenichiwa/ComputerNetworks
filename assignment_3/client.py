import time
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from threading import Thread

UDP_IP = "143.47.184.219"
UDP_PORT = 5382

SEND_INTERVAL = 2

RS_COMPLETED = 0
RS_PENDING = 1
RS_ERROR = 3

request_status = RS_COMPLETED


def main():
    ip = UDP_IP
    port = UDP_PORT

    # Logging in
    while True:
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.settimeout(1)
        username = input("Username:")
        response = log_in(username, sock, (ip, port))
        if response == f"HELLO {username}\n":
            break
            print("Logged in")
        elif response == "IN-USE\n":
            print("This username is in use")
        elif response == "BUSY\n":
            print("The server is busy")
        else:
            print("Something went wrong. Idk man.\nkthxbye")
            exit()

    # Spinning up server listening thread
    l_thread = ListeningThread(sock)
    l_thread.start()

    # Wait for user input
    while True:
        command = input()
        if command == "!quit":
            sock.close()
            exit()  # Because python has a super nifty garbage collection
        elif command == "!who":
            who(sock, (ip, port))
        elif command.startswith("@"):
            name, message = extract_name(command[1:])
            send(name, message, sock, (ip, port))


class ListeningThread(Thread):
    def __init__(self,
                 sock: socket,
                 ):
        super().__init__()
        self.socket = sock

    def run(self) -> None:
        global request_status
        while True:
            data, address = self.socket.recvfrom(2048)
            data = data.decode("utf-8")
            if data.startswith("DELIVERY "):
                name, message = extract_name(data[len("DELIVERY "):])
                print(f"{name}: {message[:-1]}")
            elif data == "BAD-RQST-HDR\n":
                request_status = RS_ERROR
                print("Bad request header")
            elif data == "BAD-RQST-BODY\n":
                request_status = RS_ERROR
                print("Bad request body")
            elif data == "SEND-OK\n":
                request_status = RS_COMPLETED
                break
            elif data == "UNKNOWN\n":
                request_status = RS_COMPLETED
                print(f"User not logged in")
                break
            elif data.startswith("WHO-OK "):
                request_status = RS_COMPLETED
                print(data[len("WHO-OK "):])


def log_in(username: str, sock: socket, address: tuple[str, int]) -> str:
    data = None
    while not data:
        msg_bytes = f"HELLO-FROM {username}\n".encode("utf-8")
        sock.sendto(msg_bytes, address)
        try:
            data, server_addr = sock.recvfrom(2048)
        except timeout as e:
            print(e)
    return data.decode("utf-8")


def send(user: str, message: str, sock: socket, address: tuple[str, int]):
    global request_status
    request_status = RS_PENDING
    start = time.time()
    now = 0
    while request_status != RS_COMPLETED:
        if request_status == RS_ERROR or start + SEND_INTERVAL > now:
            msg_bytes = f"SEND {user} {message}\n".encode("utf-8")
            sock.sendto(msg_bytes, address)
            now = time.time()


def who(sock: socket, address: tuple[str, int]):
    global request_status
    request_status = RS_PENDING
    start = time.time()
    now = 0
    while request_status != RS_COMPLETED:
        if request_status == RS_ERROR or start + SEND_INTERVAL > now:
            msg_bytes = "WHO\n".encode("utf-8")
            sock.sendto(msg_bytes, address)
            now = time.time()


def extract_name(command: str):
    if command.startswith("@"):
        without_at = command[1:]
    else:
        without_at = command
    split_index = without_at.find(' ')
    return without_at[0:split_index], without_at[split_index + 1:]


if __name__ == '__main__':
    main()
