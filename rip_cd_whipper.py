import subprocess
import os
import datetime
from pathlib import Path
import re
from dataclasses import dataclass
import sys
from rip_cd_client import send_status

WARN_AFTER_SECONDS = 60 * 60  # time the program waits before declaring a timeout
DRIVE_LABELS = {
    "/dev/disk/by-id/usb-ASUS_DRW-24D5MT_235678C218CA-0:0": "asus",
    "/dev/disk/by-id/usb-HL-DT-ST_DVDRAM_GP75N_K0ON7D64619-0:0": "sandstrom",
}
LABEL_TO_PATH = {label: path for path, label in DRIVE_LABELS.items()}
LOG_DIR = Path(__file__).resolve().parent / "logs"
NEEDS_TAGGING_FILE = Path(__file__).resolve().parent / "needs_tagging.txt"

@dataclass
class RipResult:
    success: bool
    unmatched: bool
    track_count_matched: bool
    output_path: str

@dataclass
class VerifyResult:
    counts_match: bool
    output_dir: str
    is_unmatched: bool
    disc_id: str
    is_duplicate: bool

def verify_rip(log_path):
    with open(log_path) as f:
        log_text = f.read()
    track_match_obj = re.search(r", ([0-9]+) audio tracks", log_text)
    new_rip_match = re.search(r"creating output directory (.+)", log_text)
    duplicate_match = re.search(r"output directory (.+) is a finished rip", log_text)
    unmatched_match = re.search(r"Submit this disc to MusicBrainz", log_text)
    disc_id_match = re.search(r"MusicBrainz disc id (\S+)", log_text)
    htoa_match = re.search(r"found Hidden Track \w+ Audio", log_text)
    htoa_discarded = re.search(r"HTOA discarded, contains digital silence", log_text)
    cue_match = re.search(r"parsing \.cue file '(.+\.cue)'", log_text)

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
    elif cue_match:
        print(log_path + " has no creating/duplicate marker "
              "(retry into a directory left behind by an earlier crash) "
              "- recovered output dir from the .cue file instead")
        output_dir = os.path.dirname(cue_match.group(1))
    else:
        raise ValueError("Whipper output is unexpected. Neither new nor duplicate rip. See: " + log_path)
    
    flac_files = list(Path(output_dir).glob("*.flac"))
    actual_track_count = len(flac_files)

    # HTOA is ripped-then-checked; only counts as an extra file if whipper decides it's not silence
    
    if htoa_match and not htoa_discarded:
        expected_track_count = track_match_int + 1 # bump by 1 if htoa_match and not discarded
    else:
        expected_track_count = track_match_int

    if actual_track_count == expected_track_count:
        print("Verified: Number of FLAC files as expected")
        counts_match = True
    else:
        print("Problem: Number of FLAC files not as expected")
        counts_match = False

    is_duplicate = bool(duplicate_match)

    return VerifyResult(
        counts_match=counts_match,
        output_dir=output_dir,
        is_unmatched=is_unmatched,
        disc_id=disc_id,
        is_duplicate=is_duplicate,
    )

    


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
        return (False, log_path)
    else:
        print("Rip process succeeded")
        return (True, log_path)

def record_needs_tagging(disc_id, output_dir):
    timestamp = datetime.datetime.now().isoformat()
    with open(NEEDS_TAGGING_FILE, "a") as f:
        f.write(f"{timestamp}\t{disc_id}\t{output_dir}\n") 

def rip_disc(device_path, extra_args=None):
    send_status(cased_status(status="B", device_path=device_path))
    result = None  # pessimistic default — overwritten only on success

    try:
        success, log_path = run_rip(device_path=device_path, extra_args=extra_args)
        verify_result = verify_rip(log_path)

        if verify_result.is_unmatched:
            record_needs_tagging(verify_result.disc_id, verify_result.output_dir)
            print(f"The disc could not be matched to an entry in the MusicBrainz catalogue. See {verify_result.output_dir} for details.")

        if verify_result.is_duplicate:
            overall_success = verify_result.counts_match
        else:
            overall_success = bool(success and verify_result.counts_match)

        result = RipResult(success=overall_success, unmatched=verify_result.is_unmatched,
                           track_count_matched=verify_result.counts_match, output_path=verify_result.output_dir)
    except ValueError as e:
        print(f"Something went wrong while ripping the disc: {e}")

    finally:
        if result is not None and result.success:
            send_status(cased_status(status="S", device_path=device_path))
        else:
            send_status(cased_status(status="F", device_path=device_path))

    return result


def cased_status(status, device_path):
    device = DRIVE_LABELS.get(device_path, "unknown")
    if device == "asus":
        cased_status = status.upper()
    elif device == "sandstrom":
        cased_status = status.lower()
    else:
        raise ValueError(f"Invalid device path reached signal casing decision: {device_path}")
    return cased_status

if __name__ == "__main__":
    arg = sys.argv[1]
    if arg in LABEL_TO_PATH:
        input_path = LABEL_TO_PATH.get(arg)
    else:
        raise ValueError(f"Invalid argument passed to rip_cd_whipper.py: {arg}")
    result = rip_disc(device_path=input_path)
    print(f"RipResult is: {result}")