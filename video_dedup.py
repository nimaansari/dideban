#!/usr/bin/env python3
"""
Video deduplication using perceptual hashing.
Extracts frames at 0%, 25%, 50%, 75%, 100% of video duration,
computes phash for each, stores in memory/video-hashes.json.
"""

import sys
import os
import json
import subprocess
import tempfile
import hashlib
from pathlib import Path

HASH_DB = Path(__file__).parent / "memory" / "video-hashes.json"
THRESHOLD = 10  # max hamming distance to consider duplicate (0-64)


def get_video_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except:
        return None


def extract_frame_hash(video_path, timestamp):
    """Extract a frame at given timestamp and return its phash as int."""
    import imagehash
    from PIL import Image

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["ffmpeg", "-ss", str(timestamp), "-i", video_path,
             "-vframes", "1", "-q:v", "2", tmp_path, "-y"],
            capture_output=True
        )
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return None
        img = Image.open(tmp_path)
        return str(imagehash.phash(img))
    except:
        return None
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def compute_video_fingerprint(video_path):
    """Compute perceptual hash fingerprint from 5 frames."""
    duration = get_video_duration(video_path)
    if not duration:
        return None

    positions = [0.0, 0.25, 0.5, 0.75, 0.95]
    hashes = []
    for pos in positions:
        ts = duration * pos
        h = extract_frame_hash(video_path, ts)
        if h:
            hashes.append(h)

    return hashes if hashes else None


def hamming_distance(h1, h2):
    """Compute hamming distance between two hex phash strings."""
    i1 = int(h1, 16)
    i2 = int(h2, 16)
    return bin(i1 ^ i2).count('1')


def load_db():
    if HASH_DB.exists():
        with open(HASH_DB) as f:
            return json.load(f)
    return {}


def save_db(db):
    HASH_DB.parent.mkdir(exist_ok=True)
    with open(HASH_DB, 'w') as f:
        json.dump(db, f, indent=2)


def is_duplicate(fingerprint, db):
    """Check if fingerprint matches any stored fingerprint."""
    for vid_id, stored in db.items():
        stored_hashes = stored["hashes"]
        if len(fingerprint) != len(stored_hashes):
            continue
        distances = [hamming_distance(a, b) for a, b in zip(fingerprint, stored_hashes)]
        avg_dist = sum(distances) / len(distances)
        if avg_dist <= THRESHOLD:
            return True, vid_id, avg_dist
    return False, None, None


def check_and_register(video_path):
    """
    Returns: (is_dup: bool, duplicate_of: str|None)
    If not duplicate, registers the video.
    """
    db = load_db()

    fingerprint = compute_video_fingerprint(video_path)
    if not fingerprint:
        print("ERROR: Could not extract frames from video")
        return False, None

    dup, dup_id, dist = is_duplicate(fingerprint, db)
    if dup:
        return True, dup_id

    # Register new video
    vid_id = hashlib.md5(video_path.encode()).hexdigest()[:12]
    db[vid_id] = {
        "path": video_path,
        "hashes": fingerprint
    }
    save_db(db)
    return False, None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: video_dedup.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    is_dup, dup_id = check_and_register(video_path)

    if is_dup:
        print(f"DUPLICATE:{dup_id}")
        sys.exit(1)
    else:
        print("OK")
        sys.exit(0)
