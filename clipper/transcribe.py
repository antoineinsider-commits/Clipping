"""
Transcription step: runs faster-whisper locally (free, no API) and
returns word-level timestamps, which we need both for highlight
detection (aligning the LLM's picks back to real timestamps) and
for generating karaoke-style burned-in captions.
"""

from dataclasses import dataclass, field
from typing import List

from faster_whisper import WhisperModel

from . import config

_model = None  # lazy-loaded singleton so we only pay model load cost once


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class Segment:
    text: str
    start: float
    end: float
    words: List[Word] = field(default_factory=list)


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            config.WHISPER_MODEL_SIZE,
            device=config.WHISPER_DEVICE,
            compute_type=config.WHISPER_COMPUTE_TYPE,
        )
    return _model


def transcribe(video_path: str) -> List[Segment]:
    model = _get_model()

    raw_segments, _info = model.transcribe(
        video_path,
        word_timestamps=True,
        vad_filter=True,  # skip silence, keeps timestamps tighter
    )

    segments: List[Segment] = []
    for seg in raw_segments:
        words = [
            Word(text=w.word.strip(), start=w.start, end=w.end)
            for w in (seg.words or [])
        ]
        segments.append(
            Segment(text=seg.text.strip(), start=seg.start, end=seg.end, words=words)
        )
    return segments


def to_plain_transcript(segments: List[Segment]) -> str:
    """Human/LLM-readable transcript with timestamps, e.g. for prompting."""
    lines = []
    for seg in segments:
        lines.append(f"[{seg.start:.1f}-{seg.end:.1f}] {seg.text}")
    return "\n".join(lines)
