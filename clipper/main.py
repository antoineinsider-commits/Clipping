"""
CLI entry point. Runs the full pipeline:

  ingest -> transcribe -> detect highlights -> for each highlight:
      cut -> generate + burn captions -> reframe to 9:16 -> save

Usage:
    python -m clipper.main "<video url or file path>"
    python -m clipper.main "<url>" --no-vertical --no-captions
"""

import argparse
import os
import shutil
import sys

from . import config, cut, detect, ingest, reframe, transcribe
from .captions import build_ass, burn_captions


def run(source: str, vertical: bool = True, captions: bool = True) -> list:
    print(f"[1/4] Ingesting: {source}")
    video_path = ingest.ingest(source)
    print(f"      -> {video_path}")

    print("[2/4] Transcribing (this can take a while on CPU)...")
    segments = transcribe.transcribe(video_path)
    print(f"      -> {len(segments)} segments")

    print("[3/4] Detecting highlights with local LLM...")
    highlights = detect.detect_highlights(segments)
    print(f"      -> {len(highlights)} highlights found")

    all_words = [w for seg in segments for w in seg.words]

    final_outputs = []
    for i, h in enumerate(highlights, start=1):
        print(f"[4/4] Clip {i}/{len(highlights)}: \"{h.title}\" "
              f"({h.start:.1f}s-{h.end:.1f}s, score {h.score})")

        work_subdir = os.path.join(config.WORK_DIR, f"clip_{i:02d}")
        os.makedirs(work_subdir, exist_ok=True)

        raw_clip = cut.cut_clip_output_name(work_subdir, i, h.title)
        cut.cut_clip(video_path, h.start, h.end, raw_clip)
        current = raw_clip

        if captions:
            clip_words = [w for w in all_words if h.start <= w.start <= h.end]
            ass_path = os.path.join(work_subdir, "captions.ass")
            build_ass(clip_words, h.start, ass_path)
            captioned = os.path.join(work_subdir, "captioned.mp4")
            burn_captions(current, ass_path, captioned)
            current = captioned

        if vertical:
            vertical_path = os.path.join(work_subdir, "vertical.mp4")
            reframe.reframe_to_vertical(current, vertical_path)
            current = vertical_path

        final_name = cut.cut_clip_output_name(config.OUTPUT_DIR, i, h.title)
        shutil.copy2(current, final_name)
        final_outputs.append(final_name)
        print(f"      -> saved: {final_name}")

    return final_outputs


def cli():
    parser = argparse.ArgumentParser(description="AI expert clipper")
    parser.add_argument("source", help="Video URL or local file path")
    parser.add_argument("--no-vertical", action="store_true",
                         help="Skip 9:16 reframing, keep original aspect ratio")
    parser.add_argument("--no-captions", action="store_true",
                         help="Skip burning in captions")
    args = parser.parse_args()

    outputs = run(
        args.source,
        vertical=not args.no_vertical,
        captions=not args.no_captions,
    )

    print(f"\nDone. {len(outputs)} clip(s) saved to {config.OUTPUT_DIR}/")
    for o in outputs:
        print(f"  - {o}")


if __name__ == "__main__":
    sys.exit(cli() or 0)
