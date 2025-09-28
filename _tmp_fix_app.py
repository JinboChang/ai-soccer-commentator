from pathlib import Path

path = Path("app.py")
text = path.read_text()

tts_block = "TTS_PROVIDERS = {\n    \"Default (gTTS)\": \"gtts\",\n    \"Replicate TTS\": \"replicate\",\n}\n\nSTATUS_LABELS = {\n    STATUS_FALLBACK_TTS: \"Fallback voice used\",\n    STATUS_TRIMMED_AUDIO: \"Audio trimmed\",\n    STATUS_MOCK_LLM: \"Mock commentary\",\n    STATUS_MOCK_TTS: \"Placeholder audio\",\n}\n"
new_tts_block = "TTS_PROVIDERS = {\n    \"Default (gTTS)\": \"gtts\",\n    \"Replicate TTS\": \"replicate\",\n    \"Local (pyttsx3)\": \"pyttsx3\",\n}\n\nSTATUS_LABELS = {\n    STATUS_FALLBACK_TTS: \"Fallback voice used\",\n    STATUS_TRIMMED_AUDIO: \"Audio trimmed\",\n    STATUS_MOCK_LLM: \"Mock commentary\",\n    STATUS_MOCK_TTS: \"Placeholder audio\",\n}\n"
if tts_block not in text:
    raise SystemExit("Expected TTS block not found")
path.write_text(text.replace(tts_block, new_tts_block))
