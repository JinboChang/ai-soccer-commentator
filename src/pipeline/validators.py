"""Validation helpers for uploaded media."""

from __future__ import annotations

from pathlib import Path

try:
    from moviepy.editor import VideoFileClip
except ImportError:  # moviepy>=2.0 namespace
    from moviepy.video.io.VideoFileClip import VideoFileClip

from .constants import ALLOWED_VIDEO_EXTENSIONS, MAX_VIDEO_MB, MAX_VIDEO_SECONDS
from .errors import ValidationError


def validate_extension(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError(
            message=f"Unsupported video format: {suffix or 'unknown'}",
            error_code="invalid_format",
            user_hint="Use mp4, mov, or webm clips."
        )


def validate_filesize(num_bytes: int) -> None:
    max_bytes = MAX_VIDEO_MB * 1024 * 1024
    if num_bytes > max_bytes:
        raise ValidationError(
            message=f"File exceeds {MAX_VIDEO_MB}MB limit.",
            error_code="file_too_large",
            user_hint="Upload a smaller clip (<=60MB)."
        )


def validate_duration(video_path: Path) -> float:
    clip: VideoFileClip | None = None
    try:
        clip = VideoFileClip(str(video_path))
        duration = float(clip.duration or 0.0)
    except OSError as exc:
        raise ValidationError(
            message="Unable to read video duration.",
            error_code="invalid_video",
            user_hint="Ensure the file is a playable mp4/mov/webm clip."
        ) from exc
    finally:
        if clip is not None:
            clip.close()

    if duration <= 0:
        raise ValidationError(
            message="Video appears empty.",
            error_code="zero_duration",
            user_hint="Provide a clip with visible frames."
        )

    if duration > MAX_VIDEO_SECONDS:
        raise ValidationError(
            message=f"Clip is longer than {MAX_VIDEO_SECONDS} seconds.",
            error_code="video_too_long",
            user_hint="Trim the clip to 10-30 seconds before uploading."
        )

    return duration


def validate_upload(filename: str, num_bytes: int, temp_path: Path) -> float:
    validate_extension(filename)
    validate_filesize(num_bytes)
    return validate_duration(temp_path)
