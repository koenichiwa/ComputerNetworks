import socket
import threading

listening = False

def connect(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    return sock


def disconnect(sock):
    sock.close()


def log_in(username, sock: socket):
    msg_bytes = "HELLO-FROM {}\n".format(username).encode("utf-8")
    sock.send(msg_bytes)
    return sock.recv(2048).decode("utf-8")


def send(user, message, socket):
    msg_bytes = "SEND {} {}\n".format(user, message).encode("utf-8")
    socket.send(msg_bytes)
    # return socket.recv(2048).decode("utf-8")


def who(socket):
    msg_bytes = "WHO\n".encode("utf-8")
    socket.send(msg_bytes)
    # return socket.recv(2048).decode("utf-8")


def extract_name(command):
    if command.startswith("@"):
        without_at = command[1:]
    else:
        without_at = command
    split_index = without_at.find(' ')
    return without_at[0:split_index], without_at[split_index + 1:]


def messageHandling(sock):
    while listening:
        res = sock.recv(2048).decode("utf-8")
        if res.startswith("DELIVERY "):
            name, message = extract_name(res[len("DELIVERY "):])
            print(message)
        elif res.startswith("WHO-OK"):
            print(res[len("WHO-OK "):])
        elif res == "UNKNOWN\n":
            print("User not logged in")
        elif res == "BAD-RQST-HDR\n":
            print("Bad request header")
        elif res == "BAD-RQST-BODY\n":
            print("Bad request body")


if __name__ == '__main__':
    logged_in = False

    while not logged_in:
        sock = connect("143.47.184.219", 5378)
        username = input("Username:")
        res = log_in(username, sock)
        if res.startswith("HELLO"):
            logged_in = True
            print("Logged in")
        elif res == "IN-USE\n":
            print("This username is in use")
            # disconnect(socket)
        elif res == "BUSY\n":
            print("The server is busy")
            # disconnect(socket)

    listening = True
    handleThread = threading.Thread(target=messageHandling, args=(sock,))
    handleThread.start()

    while listening:
        command = input()
        if command == "!quit":
            listening = False
        elif command == "!who":
            who(sock)
        elif command.startswith("@"):
            name, message = extract_name(command[1:])
            send(name, message, sock)

    handleThread.join()
    disconnect(socket)
