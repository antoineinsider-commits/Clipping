"""
Reframe step: converts a landscape clip to a 9:16 vertical crop for
TikTok/Reels/Shorts. Two modes:

  - "center": simple, fast, always works. Just crops around the middle.
  - "face": samples frames, finds the average face position with
    mediapipe, and centers the crop on the speaker instead of the
    geometric middle of the frame.
"""

import subprocess

import cv2

from . import config


def _get_video_dims(video_path: str):
    cap = cv2.VideoCapture(video_path)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return w, h, fps, frame_count


def _average_face_center_x(video_path: str, sample_count: int = 8) -> float:
    """Returns average face center as a fraction (0-1) of frame width.
    Falls back to 0.5 (dead center) if no faces are found or mediapipe
    isn't available."""
    try:
        import mediapipe as mp
    except ImportError:
        return 0.5

    w, h, fps, frame_count = _get_video_dims(video_path)
    if frame_count <= 0:
        return 0.5

    cap = cv2.VideoCapture(video_path)
    face_detector = mp.solutions.face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5
    )

    centers = []
    step = max(1, frame_count // sample_count)
    for i in range(sample_count):
        frame_idx = min(frame_count - 1, i * step)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ok, frame = cap.read()
        if not ok:
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_detector.process(rgb)
        if result.detections:
            # Use the first (largest/most confident) detection.
            bbox = result.detections[0].location_data.relative_bounding_box
            centers.append(bbox.xmin + bbox.width / 2)

    cap.release()
    face_detector.close()

    if not centers:
        return 0.5
    return sum(centers) / len(centers)


def reframe_to_vertical(video_path: str, output_path: str, method: str = None) -> str:
    method = method or config.REFRAME_METHOD
    w, h, _fps, _count = _get_video_dims(video_path)

    target_ratio = config.VERTICAL_WIDTH / config.VERTICAL_HEIGHT  # 9/16
    crop_w = int(h * target_ratio)
    crop_w = min(crop_w, w)  # can't crop wider than the source

    if method == "face":
        center_frac = _average_face_center_x(video_path)
    else:
        center_frac = 0.5

    center_x = center_frac * w
    x_offset = int(center_x - crop_w / 2)
    x_offset = max(0, min(w - crop_w, x_offset))

    vf = (
        f"crop={crop_w}:{h}:{x_offset}:0,"
        f"scale={config.VERTICAL_WIDTH}:{config.VERTICAL_HEIGHT}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", config.VIDEO_PRESET,
        "-crf", config.VIDEO_CRF,
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg reframe failed:\n{result.stderr[-2000:]}")

    return output_path
