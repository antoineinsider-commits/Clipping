# AI Expert Clipper

A completely free, open-source, fully local tool that turns long-form video
(podcasts, streams, talks, or any video file) into short-form clips ready
for TikTok/Reels/Shorts — automatically finding the best moments, burning
in karaoke-style captions, and reframing to 9:16 vertical.

Everything runs on your own machine. No API keys, no subscriptions, no
usage limits.

## How it works

```
URL or file
    │
    ▼
[1] Ingest        yt-dlp fetches the highest quality source available
    │
    ▼
[2] Transcribe    faster-whisper (local, free) — word-level timestamps
    │
    ▼
[3] Detect        local LLM (Ollama) scores and picks the best moments
    │
    ▼
[4] Cut           ffmpeg, frame-accurate, near-lossless quality (CRF 16)
    │
    ▼
[5] Caption       karaoke-style burned-in captions from word timestamps
    │
    ▼
[6] Reframe       crop to 9:16, optionally tracking the speaker's face
    │
    ▼
outputs/*.mp4   ← ready to upload
```

## Prerequisites

1. **Python 3.10+**
2. **ffmpeg** — must be on your PATH
   - macOS: `brew install ffmpeg`
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - Windows: [download here](https://www.gyan.dev/ffmpeg/builds/) and add to PATH
3. **Ollama** (for free local highlight detection)
   ```bash
   # install from https://ollama.com, then:
   ollama pull llama3.1
   ```
4. A GPU is optional but speeds up transcription a lot. CPU works fine
   with the `medium` Whisper model.

## Setup

```bash
git clone <this-repo-url>
cd clipper
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# From a YouTube/Twitch URL
python -m clipper.main "https://youtube.com/watch?v=..."

# From a local file
python -m clipper.main "/path/to/my_podcast.mp4"

# Keep original aspect ratio (skip 9:16 reframe)
python -m clipper.main "<source>" --no-vertical

# Skip captions
python -m clipper.main "<source>" --no-captions
```

Finished clips land in `outputs/`, named by rank and title, e.g.
`01_the_hottest_take_of_the_episode.mp4`.

## Quality notes

- Source video is always downloaded/read at the **highest available
  quality** (`yt-dlp` best video+audio streams).
- Clips are re-encoded at **CRF 16** (visually near-lossless) rather than
  stream-copied, because stream-copy cuts snap to keyframes and are
  rarely frame-accurate — not good enough for a hook-first short clip.
- Resolution is never upscaled; it's only capped on the way down (see
  `MAX_OUTPUT_HEIGHT` in `clipper/config.py`) so a 4K source doesn't
  produce unnecessarily huge files.
- Tune `VIDEO_CRF` / `VIDEO_PRESET` in `clipper/config.py` if you want to
  trade quality for faster encodes or smaller files.

## Configuration

All the knobs — Whisper model size, LLM model, clip length bounds, caption
styling, crop behavior — live in `clipper/config.py`.

## License

MIT — see [LICENSE](LICENSE).
