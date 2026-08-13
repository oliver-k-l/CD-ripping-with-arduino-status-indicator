import socket
import sys

SOCKET_PATH = "/run/discrip/discrip.sock"

def send_status(status):
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as ripcd_client:
            ripcd_client.connect(SOCKET_PATH)
            ripcd_client.sendall(status.encode())
    except OSError as e:
        print(f"send_status: failed to send {status!r} to {SOCKET_PATH}: {e}", file=sys.stderr)

if __name__ == "__main__":
    # quick manual test — read a status character from the command line
    # (sys.argv[1]) and call send_status with it, so you can test without socat
    input_arg = sys.argv[1]
    send_status(input_arg)