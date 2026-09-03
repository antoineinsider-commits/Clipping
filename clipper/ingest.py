"""
Ingest step: turns a URL or local file path into a local video file
ready for the rest of the pipeline. Always fetches/uses the highest
quality source available so downstream clips don't inherit compression
artifacts.
"""

import os
import shutil
import subprocess
from urllib.parse import urlparse

from . import config


def _is_url(s: str) -> bool:
    try:
        parsed = urlparse(s)
        return parsed.scheme in ("http", "https")
    except Exception:
        return False


def ingest(source: str) -> str:
    """
    Args:
        source: either a URL (YouTube, Twitch VOD, etc.) or a local file path.

    Returns:
        Path to a local video file, ready for transcription/cutting.
    """
    if _is_url(source):
        return _download(source)

    if not os.path.isfile(source):
        raise FileNotFoundError(f"No such file: {source}")

    # Copy into our own downloads dir so the pipeline only ever works
    # with files it owns (keeps things predictable if the original
    # file moves or gets deleted).
    dest = os.path.join(config.DOWNLOADS_DIR, os.path.basename(source))
    if os.path.abspath(source) != os.path.abspath(dest):
        shutil.copy2(source, dest)
    return dest


def _download(url: str) -> str:
    """Download the highest quality video+audio available via yt-dlp."""
    out_template = os.path.join(config.DOWNLOADS_DIR, "%(id)s.%(ext)s")

    cmd = [
        "yt-dlp",
        "-f", config.YTDLP_FORMAT,
        "--merge-output-format", "mp4",
        "--no-playlist",
        "-o", out_template,
        "--print", "after_move:filepath",
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"yt-dlp failed for {url}:\n{result.stderr.strip()}"
        )

    filepath = result.stdout.strip().splitlines()[-1]
    if not os.path.isfile(filepath):
        raise RuntimeError(f"yt-dlp reported {filepath} but it doesn't exist")

    return filepath
