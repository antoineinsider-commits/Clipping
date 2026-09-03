"""
Cutting step: slices a highlight out of the source video.

We re-encode (rather than -c copy) because stream-copy cuts snap to the
nearest keyframe and are often off by a second or more - not good enough
when the whole point is a tight, hook-first clip. Re-encoding at a low
CRF keeps quality visually lossless while giving frame-accurate cuts.
"""

import os
import subprocess

from . import config


def cut_clip(video_path: str, start: float, end: float, output_path: str) -> str:
    duration = max(0.1, end - start)

    # Cap output height so a 4K source doesn't produce enormous files,
    # but never upscale a smaller source.
    scale_filter = (
        f"scale=-2:'min({config.MAX_OUTPUT_HEIGHT},ih)'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start:.3f}",
        "-i", video_path,
        "-t", f"{duration:.3f}",
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-preset", config.VIDEO_PRESET,
        "-crf", config.VIDEO_CRF,
        "-c:a", "aac",
        "-b:a", config.AUDIO_BITRATE,
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg cut failed:\n{result.stderr[-2000:]}")

    return output_path


def cut_clip_output_name(work_dir: str, index: int, title: str) -> str:
    safe_title = "".join(c if c.isalnum() or c in " -_" else "" for c in title)
    safe_title = safe_title.strip().replace(" ", "_")[:60] or f"clip_{index}"
    return os.path.join(work_dir, f"{index:02d}_{safe_title}.mp4")
