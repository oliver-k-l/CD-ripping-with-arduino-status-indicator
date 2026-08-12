import subprocess
import os
import datetime

TIMEOUT_SECONDS = 30 * 60  # time the program waits before declaring a timeout
DRIVE_LABELS = {
    "/dev/disk/by-id/usb-ASUS_DRW-24D5MT_235678C218CA-0:0": "asus",
    "/dev/disk/by-id/usb-HL-DT-ST_DVDRAM_GP75N_K0ON7D64619-0:0": "sandstrom",
}
LOG_DIR = "logs"

def run_rip(device_path, extra_args=None, timeout=TIMEOUT_SECONDS):
    # build the base args list: whipper cd -d <device_path> rip -C complete -k
    args = ["whipper", "cd", "-d", device_path, "rip", "-C", "complete", "-k"]
    # if extra_args is given, extend the list with it (e.g. ["--cdr"])
    if extra_args is not None:
        args = args + extra_args

    device = DRIVE_LABELS.get(device_path, "unknown")

    # build the log directory (os.makedirs) and a timestamped file path
    # (os.path.join + datetime)
    os.makedirs(LOG_DIR, exist_ok=True)
    time_now = datetime.datetime.now().strftime(format="%Y%m%d_%H%M%S")
    log_path = os.path.join(LOG_DIR, device + "_" + time_now + ".log")

    latest_link = os.path.join(LOG_DIR, "latest_" + device)

    try:
        os.remove(latest_link)
    except FileNotFoundError:
        pass
    os.symlink(os.path.basename(log_path), latest_link)


    try:
        with open(log_path, "w") as log_file:

            rip_process = subprocess.run(
                args=args, stdout=log_file,
                stderr=subprocess.STDOUT,
                timeout=timeout
                )
    except subprocess.TimeoutExpired: 
        print("Disc has been ripping too long. Exiting with Timeout error")
        return False
    else:
        if rip_process.returncode != 0:
            print("rip_process failed")
            return False
        else:
            print("rip_process succeeded")
            return True

if __name__ == "__main__":
    run_rip(device_path="/dev/disk/by-id/usb-HL-DT-ST_DVDRAM_GP75N_K0ON7D64619-0:0")