from socket import socket, AF_INET, SOCK_DGRAM
from threading import Thread, Lock

UDP_IP = "143.47.184.219"
UDP_PORT = 5382

def main():
    ip = UDP_IP
    port = UDP_PORT

    # Logging in
    while not True:
        sock = socket(AF_INET, SOCK_DGRAM)
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
                 # t_address: (),
                 # t_listening
                 ):
        super().__init__()
        self.socket = sock
        # self.listening = t_listening
        # self.address = t_address

    def run(self) -> None:
        while True:
            data, address = self.socket.recvfrom(2048)
            data = data.decode("utf-8")
            if data.startswith("DELIVERY "):
                name, message = extract_name(data[len("DELIVERY "):])
                print(f"{name}: {message[:-1]}")
            elif data == "BAD-RQST-HDR\n":
                print("Bad request header")
            elif data == "BAD-RQST-BODY\n":
                print("Bad request body")


def log_in(username: str, sock: socket, address: tuple[str, int]) -> str:
    msg_bytes = f"HELLO-FROM {username}\n".encode("utf-8")
    sock.sendto(msg_bytes, address)
    data, server_addr = sock.recvfrom(2048)
    return data.decode("utf-8")


def send(user: str, message: str, sock: socket, address: tuple[str, int]):
    with Lock():
        while True:
            msg_bytes = f"SEND {user} {message}\n".encode("utf-8")
            sock.sendto(msg_bytes, address)
            data, server_addr = sock.recvfrom(2048)
            data = data.decode("utf-8")
            if data == "SEND-OK\n":
                break
            if data == "UNKNOWN\n":
                print(f"User: {user} not logged in")
                break


def who(sock: socket, address: tuple[str, int]):
    with Lock():
        msg_bytes = "WHO\n".encode("utf-8")
        sock.sendto(msg_bytes, address)
        data, server_addr = sock.recvfrom(2048)
        data = data.decode("utf-8")
        if data.startswith("WHO-OK"):
            print(data[len("WHO-OK "):])


def extract_name(command: str):
    if command.startswith("@"):
        without_at = command[1:]
    else:
        without_at = command
    split_index = without_at.find(' ')
    return without_at[0:split_index], without_at[split_index + 1:]


if __name__ == '__main__':
    main()
