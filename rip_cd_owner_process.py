import socket
import os
import serial

SOCKET_PATH = "/tmp/discrip.sock"
SERIAL_PORT = "/dev/ttyACM0"
BAUD = 9600

def main():
    # remove SOCKET_PATH if it already exists
    try:
        os.remove(SOCKET_PATH)
    except FileNotFoundError:
        pass

    # open the serial port ONCE here, with `with` — it stays open
    # for the whole life of this function
    with serial.Serial(port=SERIAL_PORT, baudrate=BAUD, timeout=5) as ser:

        # create the AF_UNIX/SOCK_STREAM socket, bind to SOCKET_PATH, listen()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as ripcd_server:
            ripcd_server.bind(SOCKET_PATH)
            ripcd_server.listen(1)        


        # loop forever:
        #   accept a connection
        #   recv() bytes from it
        #   write them straight to the serial port
        #   close the connection

            while True:
                connection, _ = ripcd_server.accept()
                data = connection.recv(16)
                ser.write(data)
                connection.close()

if __name__ == "__main__":
    main()