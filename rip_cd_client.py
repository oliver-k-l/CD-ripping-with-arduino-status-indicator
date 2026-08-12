import socket
import sys

SOCKET_PATH = "/tmp/discrip.sock"

def send_status(status):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as ripcd_client:
        ripcd_client.connect(SOCKET_PATH)
        ripcd_client.sendall(status.encode())

if __name__ == "__main__":
    # quick manual test — read a status character from the command line
    # (sys.argv[1]) and call send_status with it, so you can test without socat
    input_arg = sys.argv[1]
    send_status(input_arg)