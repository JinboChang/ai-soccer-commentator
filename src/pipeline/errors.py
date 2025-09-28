"""Custom exceptions for consistent pipeline error handling."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PipelineError(Exception):
    message: str
    error_code: str
    user_hint: str

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        return f"[{self.error_code}] {self.message}"


class ValidationError(PipelineError):
    pass


class ExternalServiceError(PipelineError):
    pass


class MuxingError(PipelineError):
    pass
