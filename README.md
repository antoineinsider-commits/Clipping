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
[3] Detect        local LLM (llama.cpp server) scores and picks the best moments
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
3. **llama.cpp** (for free local highlight detection — works on older
   Windows versions too, since it's just a console binary)
   - Download a release build from https://github.com/ggml-org/llama.cpp/releases
     (grab the Windows zip matching your CPU, e.g. `win-avx2-x64`)
   - Download a GGUF model, e.g. `Llama-3.2-3B-Instruct-Q4_K_M.gguf` from
     Hugging Face (search "bartowski Llama-3.2-3B-Instruct GGUF")
   - Start the server before running the pipeline:
     ```bash
     llama-server.exe -m Llama-3.2-3B-Instruct-Q4_K_M.gguf -c 8192 --port 8080
     ```
     Leave this running in its own terminal window while you use the clipper.
4. A GPU is optional but speeds up transcription a lot. CPU works fine
   with the `medium` Whisper model.

## Run it on GitHub instead (no local install)

Don't want to install ffmpeg/llama.cpp on your own machine at all? Push
this repo to GitHub (must be a **public** repo for free unlimited Actions
minutes) and use the included workflow:

1. Go to your repo on GitHub → the **Actions** tab
2. Click **Run AI Clipper** in the left sidebar → **Run workflow**
3. Paste a video URL, optionally check "skip captions" / "skip vertical"
4. Wait for the run to finish (transcription + LLM detection take the
   longest — expect roughly 10-30 min depending on video length)
5. Open the finished run → scroll to **Artifacts** → download `clips.zip`

This runs entirely on GitHub's free Linux runners (`.github/workflows/clip.yml`)
using Ollama instead of llama.cpp, since Ollama runs natively on Linux with
zero compatibility issues there.

## Setup (running locally)

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
