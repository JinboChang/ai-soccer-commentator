"""Orchestrates the end-to-end generation flow."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

from .errors import ExternalServiceError, MuxingError, PipelineError, ValidationError
from .llm import LLMClient
from .models import PipelineResult
from .mux import mux_audio_with_video
from .prompting import PromptContext, build_prompt
from .tts import TTSService
from .validators import validate_upload


def generate_commentated_clip(
    *,
    video_bytes: bytes,
    filename: str,
    vibe: str,
    team_a: str | None,
    team_b: str | None,
    key_moments: str | None,
    language: str | None,
    tts_provider: str | None,
    llm_client: Optional[LLMClient] = None,
    tts_service: Optional[TTSService] = None,
) -> PipelineResult:
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix or ".mp4")
    temp_video_path = Path(temp_video.name)
    with temp_video:
        temp_video.write(video_bytes)

    llm_client = llm_client or LLMClient()
    tts_service = tts_service or TTSService()

    audio_path: Path | None = None
    final_video_path: Path | None = None

    try:
        duration_s = validate_upload(filename, len(video_bytes), temp_video_path)
        prompt_ctx: PromptContext = build_prompt(
            vibe=vibe,
            team_a=team_a,
            team_b=team_b,
            key_moments=key_moments,
            language=language,
        )

        commentary_text, llm_notes = llm_client.generate(prompt_ctx.prompt, language=prompt_ctx.language)
        if not commentary_text:
            raise PipelineError(
                message="LLM produced no commentary.",
                error_code="llm_empty",
                user_hint="Retry with more context."
            )

        audio_path, tts_notes = tts_service.synthesize(
            commentary_text,
            provider=tts_provider,
            language=prompt_ctx.language,
            voice_hint=prompt_ctx.vibe_key,
        )

        final_video_path, mux_notes = mux_audio_with_video(temp_video_path, audio_path)
        temp_video_path.unlink(missing_ok=True)

        status_notes = []
        for note in llm_notes + tts_notes + mux_notes:
            if note and note not in status_notes:
                status_notes.append(note)

        return PipelineResult(
            commentary_text=commentary_text,
            audio_path=audio_path,
            video_path=final_video_path,
            duration_s=duration_s,
            status_notes=status_notes,
        )
    except (ValidationError, ExternalServiceError, MuxingError, PipelineError):
        raise
    except Exception as exc:  # pragma: no cover - defensive catch-all
        raise PipelineError(
            message="Unexpected pipeline failure.",
            error_code="pipeline_failure",
            user_hint="Please retry; if the issue persists, contact support."
        ) from exc
    finally:
        if temp_video_path.exists():
            temp_video_path.unlink(missing_ok=True)
        if final_video_path is None and audio_path is not None:
            audio_path.unlink(missing_ok=True)
