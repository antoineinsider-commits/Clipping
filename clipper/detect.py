"""
Highlight detection: the "expert clipper" brain. Feeds the timestamped
transcript to a local LLM (served by llama.cpp's llama-server - completely
free, runs on your own machine, no API keys) and asks it to pick the
segments most worth clipping, scored by how likely they are to hook a viewer.
"""

import json
import re
from dataclasses import dataclass
from typing import List

import requests

from . import config
from .transcribe import Segment

PROMPT_TEMPLATE = """You are an expert short-form video editor who has cut \
thousands of viral TikTok/Reels/Shorts clips from long-form podcasts and \
streams. Below is a timestamped transcript of a video.

Find the {max_clips} best moments to cut into standalone short clips. \
A great clip has a strong hook in the first 2-3 seconds, a self-contained \
story or point (doesn't require earlier context to make sense), and an \
emotional peak, punchline, hot take, or surprising moment. Each clip should \
be between {min_len} and {max_len} seconds long.

Respond with ONLY a JSON array, no other text, in this exact format:
[
  {{"start": 123.4, "end": 178.9, "score": 8.5, "title": "short punchy title", "reason": "why this clip works"}}
]

Transcript:
{transcript}
"""


@dataclass
class Highlight:
    start: float
    end: float
    score: float
    title: str
    reason: str


def _call_llm(prompt: str) -> str:
    """Calls llama.cpp's llama-server, which exposes an OpenAI-compatible
    /v1/chat/completions endpoint. Make sure the server is running first:
    llama-server.exe -m your-model.gguf -c 8192 --port 8080
    """
    resp = requests.post(
        config.LLM_SERVER_URL,
        json={
            "model": config.LLM_MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "stream": False,
        },
        timeout=600,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _extract_json_array(text: str) -> list:
    """LLMs sometimes wrap JSON in prose or code fences - pull the array out."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in LLM response:\n{text}")
    return json.loads(match.group(0))


def detect_highlights(segments: List[Segment]) -> List[Highlight]:
    from .transcribe import to_plain_transcript  # local import avoids a cycle

    transcript = to_plain_transcript(segments)
    prompt = PROMPT_TEMPLATE.format(
        max_clips=config.MAX_CLIPS_PER_VIDEO,
        min_len=config.MIN_CLIP_SECONDS,
        max_len=config.MAX_CLIP_SECONDS,
        transcript=transcript,
    )

    raw = _call_llm(prompt)
    items = _extract_json_array(raw)

    highlights = []
    video_end = segments[-1].end if segments else 0

    for item in items:
        try:
            start = float(item["start"])
            end = float(item["end"])
        except (KeyError, TypeError, ValueError):
            continue

        # Sanity-clamp against the actual video length and length bounds.
        start = max(0.0, start)
        end = min(video_end, end)
        length = end - start
        if length < config.MIN_CLIP_SECONDS or length > config.MAX_CLIP_SECONDS * 1.5:
            continue

        highlights.append(
            Highlight(
                start=start,
                end=end,
                score=float(item.get("score", 0)),
                title=str(item.get("title", "clip")).strip(),
                reason=str(item.get("reason", "")).strip(),
            )
        )

    highlights.sort(key=lambda h: h.score, reverse=True)
    return highlights[: config.MAX_CLIPS_PER_VIDEO]
