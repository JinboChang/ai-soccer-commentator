"""Data containers used across the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


@dataclass
class PipelineResult:
    commentary_text: str
    audio_path: Path
    video_path: Path
    duration_s: float
    status_notes: list[str] = field(default_factory=list)

    def cleanup(self, extra_paths: Iterable[Path] | None = None) -> None:
        paths: List[Path] = [self.audio_path, self.video_path]
        if extra_paths:
            paths.extend(list(extra_paths))
        for file_path in paths:
            try:
                file_path.unlink(missing_ok=True)
            except Exception:  # pragma: no cover - cleanup best effort
                pass
