import time
from socket import socket, AF_INET, SOCK_DGRAM, timeout
from threading import Thread

UDP_IP = "143.47.184.219"
UDP_PORT = 5382

SEND_INTERVAL = 2  # seconds

RS_COMPLETED = 0
RS_PENDING = 1
RS_ERROR = 2

request_status = RS_COMPLETED


def main():
    ip = UDP_IP
    port = UDP_PORT

    # Logging in
    sock = socket(AF_INET, SOCK_DGRAM)
    # TODO: set time out here?
    # sock.settimeout(1)
    log_in(sock, (ip, port))


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
            data = receive_data(self.socket, 2048)
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
            else:
                print(f"Unknown server response: {data}")


def log_in(sock: socket, address: tuple[str, int]):
    while True:
        username = input("Username: ")
        msg_bytes = f"HELLO-FROM {username}\n".encode("utf-8")
        sock.sendto(msg_bytes, address)
        data = receive_data(sock, 2048)
        if data == f"HELLO {username}\n":
            print("Logged in.")
            break
        elif data == "IN-USE\n":
            print("This username is in use. Try again.")
        elif data == "BUSY\n":
            print("The server is busy.")
            print("Exiting client.")
            exit()
        else:
            print("Something went wrong. Reason unknown.")
            print("Exiting client.")
            exit()





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


def receive_data(sock: socket, bufsize: int):
    # TODO: maybe timeout?
    data, address = sock.recvfrom(bufsize)
    # TODO: check for bitflips
    data = data.decode("utf-8")
    return data


if __name__ == '__main__':
    main()
