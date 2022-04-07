import socket
import threading

DEFAULT_IP = "143.47.184.219"
DEFAULT_PORT = 5378

LOCAL_IP = "localhost"
LOCAL_PORT = 4242


class ListeningThread(threading.Thread):
    def __init__(self, t_socket, t_listening):
        super().__init__()
        self.socket = t_socket
        self.listening = t_listening

    def run(self) -> None:
        while self.listening:
            res = sock.recv(2048).decode("utf-8")
            if res.startswith("DELIVERY "):
                name, message = extract_name(res[len("DELIVERY "):])
                print(f"{name}: {message[:-1]}")
            elif res.startswith("WHO-OK"):
                print(res[len("WHO-OK "):])
            elif res == "UNKNOWN\n":
                print("User not logged in")
            elif res == "BAD-RQST-HDR\n":
                print("Bad request header")
            elif res == "BAD-RQST-BODY\n":
                print("Bad request body")


def connect(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    return sock


# def disconnect(sock):
#     sock.close()


def log_in(username, sock: socket):
    msg_bytes = f"HELLO-FROM {username}\n".encode("utf-8")
    sock.sendall(msg_bytes)
    return sock.recv(2048).decode("utf-8")


def send(user, message, socket):
    msg_bytes = f"SEND {user} {message}\n".encode("utf-8")
    socket.sendall(msg_bytes)


def who(socket):
    msg_bytes = "WHO\n".encode("utf-8")
    socket.sendall(msg_bytes)


def extract_name(command):
    if command.startswith("@"):
        without_at = command[1:]
    else:
        without_at = command
    split_index = without_at.find(' ')
    return without_at[0:split_index], without_at[split_index + 1:]


if __name__ == '__main__':
    # Choose <ip>:<port>. Making it easier for assignment 2
    connection_type = input("""
How would you like to connect?
1: Default server
2: Local Server
<ip>:<portnumber>
""")
    if connection_type == "1":
        ip, port = DEFAULT_IP, DEFAULT_PORT
    elif connection_type == "2":
        ip, port = LOCAL_IP, LOCAL_PORT
    else:
        try:
            connection_values = connection_type.split(":")
            ip = connection_values[0]
            port = int(connection_values[1])
        except (ValueError, IndexError):
            print("Wrong syntax\nShutting down client....")
            exit()

    # Connecting and logging in
    logged_in = False
    while not logged_in:
        try:
            sock = connect(ip, port)
        except ConnectionRefusedError:
            print(f"Can't connect to {ip}:{port}\nShutting down client....")
            exit()
        username = input("Username:")
        res = log_in(username, sock)
        if res.startswith("HELLO"):
            logged_in = True
            print("Logged in")
        elif res == "IN-USE\n":
            print("This username is in use")
        elif res == "BUSY\n":
            print("The server is busy")

    # Spinning up server listening thread
    l_thread = ListeningThread(sock, True)
    l_thread.start()

    # Wait for user input
    while True:
        command = input()
        if command == "!quit":
            exit()  # Because python has a super nifty garbage collection
        elif command == "!who":
            who(sock)
        elif command.startswith("@"):
            name, message = extract_name(command[1:])
            send(name, message, sock)
