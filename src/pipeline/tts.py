"""Text-to-speech handling with fallbacks."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterable, Tuple

import requests
from gtts import gTTS

from .constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_TTS_PROVIDER,
    GTTS_TLD_BY_VIBE,
    REPLICATE_TTS_MODEL,
    STATUS_FALLBACK_TTS,
    STATUS_MOCK_TTS,
)
from .errors import ExternalServiceError

try:  # pragma: no cover - optional dependency
    import replicate  # type: ignore
except ImportError:  # pragma: no cover - fallback path
    replicate = None  # type: ignore


class TTSService:
    def __init__(
        self,
        *,
        default_provider: str | None = None,
        allow_mock_fallback: bool = True,
    ) -> None:
        self.default_provider = (default_provider or DEFAULT_TTS_PROVIDER).lower()
        self.allow_mock_fallback = allow_mock_fallback
        self.replicate_model = os.getenv("REPLICATE_TTS_MODEL", REPLICATE_TTS_MODEL)
        self.api_token = os.getenv("REPLICATE_API_TOKEN")

    def synthesize(
        self,
        text: str,
        *,
        provider: str | None,
        language: str | None,
        voice_hint: str,
    ) -> Tuple[Path, list[str]]:
        provider_key = (provider or self.default_provider or DEFAULT_TTS_PROVIDER).lower()
        if provider_key not in {"gtts", "replicate", "pyttsx3"}:
            provider_key = "gtts"

        notes: list[str] = []
        language_code = (language or DEFAULT_LANGUAGE).split("-")[0]
        vibe_key = (voice_hint or "").lower()
        gtts_tld = self._resolve_gtts_tld(vibe_key=vibe_key, language_code=language_code)

        provider_chain = self._build_provider_chain(provider_key)
        last_exception: Exception | None = None

        for active_provider in provider_chain:
            try:
                if active_provider == "replicate":
                    audio_path = self._synthesize_replicate(text, language_code, voice_hint)
                    return audio_path, notes
                if active_provider == "gtts":
                    audio_path = self._synthesize_gtts(text, language_code, gtts_tld)
                    return audio_path, notes
                if active_provider == "pyttsx3":
                    audio_path = self._synthesize_pyttsx3(text, language_code, vibe_key)
                    return audio_path, notes
            except Exception as exc:  # pragma: no cover - runtime/path issues
                last_exception = exc
                if active_provider != provider_chain[-1]:
                    notes.append(STATUS_FALLBACK_TTS)
                continue

        if not self.allow_mock_fallback:
            raise ExternalServiceError(
                message="TTS generation failed.",
                error_code="tts_failure",
                user_hint="Try switching voice provider."
            ) from last_exception

        notes.append(STATUS_MOCK_TTS)
        audio_path = self._generate_placeholder_audio()
        return audio_path, notes

    def _build_provider_chain(self, primary: str) -> list[str]:
        chain: list[str] = []

        def add(provider: str) -> None:
            if provider not in chain:
                chain.append(provider)

        if primary == "replicate":
            if self.api_token and self.replicate_model and replicate is not None:
                add("replicate")
            add("gtts")
            add("pyttsx3")
        elif primary == "gtts":
            add("gtts")
            add("pyttsx3")
        elif primary == "pyttsx3":
            add("pyttsx3")
            add("gtts")
        else:
            add("gtts")
            add("pyttsx3")

        return chain

    def _resolve_gtts_tld(self, *, vibe_key: str, language_code: str) -> str:
        tld = GTTS_TLD_BY_VIBE.get(vibe_key, "com")
        if language_code.startswith("es"):
            return "com.mx"
        if language_code.startswith("ko"):
            return "co.kr"
        return tld

    def _synthesize_gtts(self, text: str, language_code: str, tld: str) -> Path:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        with temp_file as fh:
            tts = gTTS(text=text, lang=language_code, tld=tld)
            tts.write_to_fp(fh)
        return Path(temp_file.name)

    def _synthesize_replicate(self, text: str, language_code: str, voice_hint: str) -> Path:
        if not self.api_token or not self.replicate_model or replicate is None:
            raise ExternalServiceError(
                message="Replicate TTS unavailable (missing token or model).",
                error_code="replicate_tts_unconfigured",
                user_hint="Provide REPLICATE_API_TOKEN and REPLICATE_TTS_MODEL."
            )

        client = replicate.Client(api_token=self.api_token)
        output = client.run(
            self.replicate_model,
            input={"text": text, "voice": voice_hint, "language": language_code},
        )

        audio_bytes: bytes | None = None
        url_candidates: Iterable[str] = []
        if isinstance(output, (list, tuple)):
            url_candidates = [str(item) for item in output]
        elif isinstance(output, str):
            url_candidates = [output]
        elif isinstance(output, dict):
            data = output.get("audio") or output.get("url")
            if isinstance(data, str):
                url_candidates = [data]

        for candidate in url_candidates:
            if candidate.startswith("http"):
                response = requests.get(candidate, timeout=20)
                response.raise_for_status()
                audio_bytes = response.content
                break

        if audio_bytes is None and isinstance(output, (bytes, bytearray)):
            audio_bytes = bytes(output)

        if audio_bytes is None:
            raise ExternalServiceError(
                message="Replicate TTS did not return audio bytes.",
                error_code="replicate_tts_empty",
                user_hint="Try again or switch to default voice."
            )

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        with temp_file as fh:
            fh.write(audio_bytes)
        return Path(temp_file.name)

    def _synthesize_pyttsx3(self, text: str, language_code: str, vibe_key: str) -> Path:
        try:
            import pyttsx3  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise ExternalServiceError(
                message="Local TTS (pyttsx3) is not installed.",
                error_code="pyttsx3_missing",
                user_hint="Run `pip install pyttsx3` and retry."
            ) from exc

        engine = pyttsx3.init()
        voice_id = self._select_pyttsx3_voice(engine, language_code, vibe_key)
        if voice_id:
            engine.setProperty("voice", voice_id)

        engine.setProperty("rate", self._resolve_pyttsx3_rate(vibe_key))
        engine.setProperty("volume", 1.0)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = Path(temp_file.name)
        temp_file.close()
        engine.save_to_file(text, str(temp_path))
        engine.runAndWait()
        engine.stop()
        return temp_path

    def _select_pyttsx3_voice(self, engine: "pyttsx3.Engine", language_code: str, vibe_key: str) -> str | None:
        voices = engine.getProperty("voices")
        tokens = []
        if language_code.startswith("es") or vibe_key == "latin radio":
            tokens = ["es"]
        elif language_code.startswith("ko"):
            tokens = ["ko"]
        elif vibe_key == "british pundit":
            tokens = ["en-gb", "english"]
        else:
            tokens = ["en"]

        for voice in voices:
            sample = " ".join([
                voice.id.lower(),
                voice.name.lower(),
                " ".join(str(lang).lower() for lang in getattr(voice, "languages", [])),
            ])
            if all(token in sample for token in tokens):
                return voice.id
        return None

    def _resolve_pyttsx3_rate(self, vibe_key: str) -> int:
        if vibe_key == "latin radio":
            return 210
        if vibe_key == "hype":
            return 195
        if vibe_key == "british pundit":
            return 175
        if vibe_key == "calm analysis":
            return 165
        return 185

    def _generate_placeholder_audio(self) -> Path:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        sample_rate = 16000
        duration_seconds = 2
        total_frames = sample_rate * duration_seconds
        import wave
        import array

        with wave.open(temp_file, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            silence = array.array("h", [0] * total_frames)
            wav_file.writeframes(silence.tobytes())

        return Path(temp_file.name)
