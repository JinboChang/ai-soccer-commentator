from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.pipeline.processor import generate_commentated_clip


def run_smoke(video_path: Path) -> None:
    if not video_path.exists():
        raise FileNotFoundError(f"Sample clip not found: {video_path}")

    load_dotenv()
    with video_path.open("rb") as fh:
        video_bytes = fh.read()

    result = generate_commentated_clip(
        video_bytes=video_bytes,
        filename=video_path.name,
        vibe="hype",
        team_a="Sample United",
        team_b="Demo FC",
        key_moments="Quick break, curling finish",
        language="en",
        tts_provider=os.getenv("TTS_PROVIDER", "gtts"),
    )
    print("Commentary:", result.commentary_text)
    print("Status notes:", result.status_notes)
    print("Audio path:", result.audio_path)
    print("Video path:", result.video_path)
    result.cleanup()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a local smoke test clip through the pipeline.")
    parser.add_argument("video", type=Path, help="Path to a 10-30s silent soccer sample clip.")
    args = parser.parse_args()
    run_smoke(args.video)
