import time
import serial

PORT = "/dev/ttyACM0"
BAUD = 9600

t0 = time.monotonic()

with serial.Serial(port=PORT, baudrate=BAUD, timeout=10) as ser:
    while True:
        line = ser.readline()
        if "READY" in repr(line):
            t1 = time.monotonic()
            break

print(f"{t1 - t0:.3f} s")