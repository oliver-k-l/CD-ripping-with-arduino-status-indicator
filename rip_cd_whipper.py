import subprocess
import os
import datetime
from pathlib import Path
import re

WARN_AFTER_SECONDS = 60 * 60  # time the program waits before declaring a timeout
DRIVE_LABELS = {
    "/dev/disk/by-id/usb-ASUS_DRW-24D5MT_235678C218CA-0:0": "asus",
    "/dev/disk/by-id/usb-HL-DT-ST_DVDRAM_GP75N_K0ON7D64619-0:0": "sandstrom",
}
LOG_DIR = Path(__file__).resolve().parent / "logs"
NEEDS_TAGGING_FILE = Path(__file__).resolve().parent / "needs_tagging.txt"


def verify_rip(log_path):
    with open(log_path) as f:
        log_text = f.read()
    track_match_obj = re.search(r", ([0-9]+) audio tracks", log_text)
    new_rip_match = re.search(r"creating output directory (.+)", log_text)
    duplicate_match = re.search(r"output directory (.+) is a finished rip", log_text)
    unmatched_match = re.search(r"Submit this disc to MusicBrainz", log_text)
    disc_id_match = re.search(r"MusicBrainz disc id (\S+)", log_text)

    is_unmatched = bool(unmatched_match)

    if disc_id_match:
        disc_id = disc_id_match.group(1)
    else:
        raise ValueError("Whipper output unexpected. For details, see: " + log_path)

    if track_match_obj:
        track_match_int = int(track_match_obj.group(1))
    else:
        raise ValueError("Whipper output shows no number of tracks. For details, see: " + log_path)

    if new_rip_match:
        output_dir = new_rip_match.group(1)
    elif duplicate_match:
        print(log_path + " is a finished rip")
        output_dir = duplicate_match.group(1)
    else:
        raise ValueError("Whipper output is unexpected. Neither new nor duplicate rip. See: " + log_path)

    flac_files = list(Path(output_dir).glob("*.flac"))
    actual_track_count = len(flac_files)

    if actual_track_count == track_match_int:
        print("Verified: Number of FLAC files as expected")
        counts_match = True
    else:
        print("Problem: Number of FLAC files not as expected")
        counts_match = False

    return (counts_match, output_dir, is_unmatched, disc_id)

    


def run_rip(device_path, extra_args=None, warn_after=WARN_AFTER_SECONDS):
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

    with open(log_path, "w") as log_file:
        # Popen starts the child and returns immediately — does NOT block
        rip_process = subprocess.Popen(
            args, stdout=log_file, stderr=subprocess.STDOUT
        )

        try:
            # blocks until finished, OR until warn_after seconds pass
            rip_process.wait(timeout=warn_after)
        except subprocess.TimeoutExpired:
            print(f"Attention: This disc has been ripping for {WARN_AFTER_SECONDS/60} minutes")
            rip_process.wait()

    if rip_process.returncode != 0:
        print("Rip process failed")
        return False
    else:
        print("Rip process succeeded")
        return True

def record_needs_tagging(disc_id, output_dir):
    timestamp = datetime.datetime.now().isoformat()
    with open(NEEDS_TAGGING_FILE, "a") as f:
        f.write(f"{timestamp}\t{disc_id}\t{output_dir}\n") 

if __name__ == "__main__":
    run_rip(device_path="/dev/disk/by-id/usb-HL-DT-ST_DVDRAM_GP75N_K0ON7D64619-0:0")