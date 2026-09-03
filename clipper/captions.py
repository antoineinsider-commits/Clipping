"""
Captions step: builds karaoke-style burned-in captions (each word pops/
highlights as it's spoken, like CapCut auto-captions) from Whisper's
word-level timestamps, then burns them into the clip with ffmpeg.
"""

import os
import subprocess
from typing import List

from . import config
from .transcribe import Word

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: {play_res_y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},{base_color},&H000000FF,{outline_color},&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,60,60,220,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _fmt_ts(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _group_words_into_lines(words: List[Word], max_words_per_line: int = 4):
    """Group words into short 3-4 word bursts - reads better on a phone
    screen than full sentences, and matches the punchy captioning style
    used across TikTok/Reels editors."""
    lines = []
    for i in range(0, len(words), max_words_per_line):
        lines.append(words[i : i + max_words_per_line])
    return lines


def build_ass(words: List[Word], clip_start_offset: float, output_path: str) -> str:
    """
    Args:
        words: word-level timestamps, in the ORIGINAL source video's time base.
        clip_start_offset: the clip's start time in the source video, so we
            can shift word timestamps to be relative to the clip itself.
    """
    header = ASS_HEADER.format(
        play_res_y=config.CAPTION_PLAY_RES_Y,
        font=config.CAPTION_FONT,
        size=config.CAPTION_FONT_SIZE,
        base_color=config.CAPTION_BASE_COLOR,
        outline_color=config.CAPTION_OUTLINE_COLOR,
    )

    events = []
    for line_words in _group_words_into_lines(words):
        if not line_words:
            continue
        line_start = line_words[0].start - clip_start_offset
        line_end = line_words[-1].end - clip_start_offset
        if line_end <= 0:
            continue
        line_start = max(0.0, line_start)

        # Karaoke tags (\k) highlight each word as it's spoken. Duration
        # is in centiseconds.
        karaoke_text = ""
        for w in line_words:
            dur_cs = max(1, int(round((w.end - w.start) * 100)))
            karaoke_text += f"{{\\k{dur_cs}}}{w.text} "

        events.append(
            f"Dialogue: 0,{_fmt_ts(line_start)},{_fmt_ts(line_end)},Default,,0,0,0,,{karaoke_text.strip()}"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n".join(events))
        f.write("\n")

    return output_path


def burn_captions(video_path: str, ass_path: str, output_path: str) -> str:
    # ffmpeg's ass filter needs a POSIX-friendly, escaped path on some
    # platforms - simplest reliable approach is to cd into the ass file's dir.
    ass_dir = os.path.dirname(os.path.abspath(ass_path)) or "."
    ass_name = os.path.basename(ass_path)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"ass={ass_name}",
        "-c:v", "libx264",
        "-preset", config.VIDEO_PRESET,
        "-crf", config.VIDEO_CRF,
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=ass_dir)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg caption burn failed:\n{result.stderr[-2000:]}")

    return output_path
