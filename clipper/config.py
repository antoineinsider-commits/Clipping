"""
Central configuration for the AI clipper pipeline.
Tweak these values to trade off speed vs quality vs output style.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
WORK_DIR = os.path.join(BASE_DIR, "work")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

for _d in (DOWNLOADS_DIR, WORK_DIR, OUTPUT_DIR):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------------------
# Transcription (faster-whisper)
# ---------------------------------------------------------------------------
# Model size: tiny / base / small / medium / large-v3
# large-v3 is most accurate but slower. medium is a good speed/accuracy balance
# on a laptop CPU. Use large-v3 if you have a decent GPU.
WHISPER_MODEL_SIZE = "medium"
WHISPER_DEVICE = "auto"       # "cuda" if you have an NVIDIA GPU, else "cpu"
WHISPER_COMPUTE_TYPE = "auto"  # "float16" on GPU, "int8" on CPU for speed

# ---------------------------------------------------------------------------
# Highlight detection (local LLM via Ollama - completely free, no API keys)
# ---------------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1"      # run `ollama pull llama3.1` first
MAX_CLIP_SECONDS = 90          # don't let a single clip run longer than this
MIN_CLIP_SECONDS = 12          # discard anything shorter than this
MAX_CLIPS_PER_VIDEO = 8        # cap how many highlights we cut per source video

# ---------------------------------------------------------------------------
# Video output quality
# ---------------------------------------------------------------------------
# CRF: lower = higher quality / bigger file. 16-18 is visually near-lossless.
VIDEO_CRF = "16"
VIDEO_PRESET = "slow"          # slower = better compression efficiency at same CRF
AUDIO_BITRATE = "192k"
# Keep the source resolution - never upscale, never downscale unless the
# source is absurdly large (>1440p), to keep file sizes sane.
MAX_OUTPUT_HEIGHT = 1440

# yt-dlp format selector: best available video + best available audio,
# preferring mp4/h264 containers for compatibility.
YTDLP_FORMAT = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best"

# ---------------------------------------------------------------------------
# Reframe (landscape -> 9:16 vertical)
# ---------------------------------------------------------------------------
REFRAME_METHOD = "face"        # "center" or "face"
VERTICAL_WIDTH = 1080
VERTICAL_HEIGHT = 1920

# ---------------------------------------------------------------------------
# Captions
# ---------------------------------------------------------------------------
CAPTION_FONT = "Arial Black"
CAPTION_FONT_SIZE = 20          # in ASS units, scales with PlayResY below
CAPTION_PLAY_RES_Y = 1920
CAPTION_HIGHLIGHT_COLOR = "&H0000D7FF"  # gold/yellow (BGR hex, ASS format)
CAPTION_BASE_COLOR = "&H00FFFFFF"       # white
CAPTION_OUTLINE_COLOR = "&H00000000"    # black outline
