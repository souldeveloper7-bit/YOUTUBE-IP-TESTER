#!/usr/bin/env python3
"""
All-in-one YouTube IP + download tester.
No hosting Variables / environment setup required.

Run:
  python ip_tester_all_in_one.py

It asks for a YouTube URL only if stdin is interactive. In hosted/non-interactive
execution, it uses the built-in TEST_VIDEO_URL below.
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

# Put a public YouTube video URL here if you want to change the test video.
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=gVCyoPjEZG0"


def public_ip():
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode().strip()
        except Exception:
            pass
    return "Could not detect public IP"


def run_ytdlp(args):
    try:
        return subprocess.run(
            [sys.executable, "-m", "yt_dlp", *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
        )
    except subprocess.TimeoutExpired:
        return None


def main():
    print("=== YOUTUBE IP + DOWNLOAD TEST ===", flush=True)
    print("Public IP:", public_ip(), flush=True)

    url = TEST_VIDEO_URL.strip()
    # On a terminal, let the user optionally enter a different URL.
    try:
        if sys.stdin is not None and sys.stdin.isatty():
            entered = input("YouTube URL (Enter = built-in test video): ").strip()
            if entered:
                url = entered
    except (EOFError, OSError):
        pass

    print("Test video:", url, flush=True)

    version = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if version.returncode != 0:
        print("yt-dlp is missing. Install it with: pip install yt-dlp")
        return
    print("yt-dlp version:", version.stdout.strip(), flush=True)

    print("\\n[1/2] Checking YouTube metadata access...", flush=True)
    info = run_ytdlp([
        "--no-warnings", "--skip-download", "--dump-single-json", url
    ])
    if info is None:
        print("FAILED: metadata request timed out.")
        return
    if info.returncode:
        print("FAILED: YouTube metadata request was rejected.")
        print("\\n".join(info.stderr.strip().splitlines()[-8:]))
        print("\\nRESULT: this IP/session did not pass the YouTube test.")
        return

    try:
        title = json.loads(info.stdout).get("title", "Unknown title")
    except Exception:
        title = "Video metadata received"
    print("OK:", title, flush=True)

    print("\\n[2/2] Trying a short 5-second download...", flush=True)
    out_dir = Path("yt_ip_test_download")
    out_dir.mkdir(exist_ok=True)
    result = run_ytdlp([
        "--no-warnings", "--no-playlist",
        "--download-sections", "*0-5",
        "-f", "best[ext=mp4]/best",
        "-o", str(out_dir / "test.%(ext)s"),
        url,
    ])
    if result is None:
        print("FAILED: download timed out.")
        return
    if result.returncode:
        print("FAILED: metadata worked, but download failed.")
        print("\\n".join(result.stderr.strip().splitlines()[-8:]))
        return

    files = [
        f for f in out_dir.glob("test.*")
        if f.is_file() and f.stat().st_size > 0
    ]
    if files:
        print("SUCCESS: test download worked:", files[0], flush=True)
        print("File size:", files[0].stat().st_size, "bytes")
        print("RESULT: IP passed at this moment.")
    else:
        print("yt-dlp finished, but no test file was found.")

    print("\\nNote: YouTube can block/challenge this IP later. This script does not bypass restrictions.")


if __name__ == "__main__":
    main()
