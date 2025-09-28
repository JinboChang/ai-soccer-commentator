"""Constants and mappings for the AI commentator pipeline."""

from __future__ import annotations

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm"}
MAX_VIDEO_MB = 60
MAX_VIDEO_SECONDS = 30
DEFAULT_LANGUAGE = "en"
DEFAULT_TTS_PROVIDER = "gtts"
REPLICATE_LLM_MODEL = "meta/meta-llama-3-8b-instruct"
REPLICATE_TTS_MODEL = ""  # Fill with preferred model identifier when available

VIBE_PROMPTS = {
    "hype": "Maximum adrenaline, breathless goal call, celebrate the moment like a cup final.",
    "calm analysis": "Measured insight with rising excitement, weaving tactics into the play-by-play.",
    "british pundit": "Classic Premier League drama, vivid metaphors, clipped delivery with punchy exclamations.",
    "latin radio": "Rapid-fire castellano, rolling r's, elongated goal shouts, crowd-swept emotion."
}

GTTS_TLD_BY_VIBE = {
    "hype": "com",
    "calm analysis": "com",
    "british pundit": "co.uk",
    "latin radio": "com.mx",
}

STATUS_FALLBACK_TTS = "Used fallback TTS"
STATUS_TRIMMED_AUDIO = "Trimmed audio to video length"
STATUS_MOCK_LLM = "Used mock commentary generator"
STATUS_MOCK_TTS = "Rendered placeholder audio"
