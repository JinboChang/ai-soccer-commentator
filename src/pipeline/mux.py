"""Muxing helpers to combine generated audio with the uploaded video."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Tuple

try:
    from moviepy.editor import AudioFileClip, VideoFileClip
except ImportError:  # moviepy>=2.0 namespace
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.video.io.VideoFileClip import VideoFileClip

from .constants import STATUS_TRIMMED_AUDIO
from .errors import MuxingError


def mux_audio_with_video(video_path: Path, audio_path: Path) -> Tuple[Path, list[str]]:
    output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output_path = Path(output_file.name)
    output_file.close()

    video_clip: VideoFileClip | None = None
    audio_clip: AudioFileClip | None = None
    notes: list[str] = []

    try:
        video_clip = VideoFileClip(str(video_path))
        audio_clip = AudioFileClip(str(audio_path))

        trimmed = False
        if audio_clip.duration and video_clip.duration and audio_clip.duration > video_clip.duration:
            if hasattr(audio_clip, "subclip"):
                audio_clip = audio_clip.subclip(0, video_clip.duration)
            else:
                audio_clip = audio_clip.subclipped(0, video_clip.duration)
            trimmed = True

        if hasattr(video_clip, "set_audio"):
            result_clip = video_clip.set_audio(audio_clip)
        else:
            result_clip = video_clip.with_audio(audio_clip)

        fps = video_clip.fps or 30
        write_kwargs = {"codec": "libx264", "audio_codec": "aac", "fps": fps}
        result_clip.write_videofile(str(output_path), **write_kwargs)

        if trimmed:
            notes.append(STATUS_TRIMMED_AUDIO)
        return output_path, notes
    except Exception as exc:  # pragma: no cover - external dependency
        raise MuxingError(
            message="Could not mux audio and video.",
            error_code="mux_failure",
            user_hint="Ensure ffmpeg is installed and retry."
        ) from exc
    finally:
        if video_clip is not None:
            video_clip.close()
        if audio_clip is not None:
            audio_clip.close()
