# AI Football Commentator

Turn short silent soccer clips into lively, narrated highlight reels directly in the browser. This MVP pairs Streamlit for the UI with Replicate (LLM + optional TTS), gTTS fallback, and moviepy+ffmpeg muxing.

## Features

- Upload 10-30 second mp4/mov/webm clips (<=60MB)
- Pick a commentary vibe (Hype, Calm analysis, British pundit, Latin radio)
- Optional team names and key-moment hints steer the narration
- Generates short-form commentary text via Replicate LLM (mock fallback without a token)
- Synthesises commentary audio (Replicate TTS, gTTS, or offline pyttsx3 with graceful fallbacks)
- Muxes the new audio track onto the uploaded clip and makes both assets downloadable
- Displays status chips (fallback voice, trimmed audio, mock commentary)

## Requirements

- Python 3.10+
- ffmpeg available on PATH (moviepy relies on it)
- Optional Replicate credentials for higher-quality LLM/TTS

## Quick start

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env  # edit values as needed
streamlit run app.py
```

Open the URL shown by Streamlit (default: `http://localhost:8501`). Upload a silent soccer clip, choose the vibe, and click **Generate commentary**. The page shows the generated script, audio preview, and combined MP4 plus download buttons.

## Environment variables

Set these in `.env` or your host environment:

- `REPLICATE_API_TOKEN`: required for live Replicate calls. Without it the app will return deterministic mock commentary text.
- `REPLICATE_LLM_MODEL`: overrides the default `meta/meta-llama-3-8b-instruct`.
- `REPLICATE_TTS_MODEL`: optional Replicate voice model. If missing, the app falls back to gTTS.

## Error handling & fallbacks

- File validation rejects unsupported formats, clips >60MB, and videos longer than 30 seconds.
- LLM issues: retries once on transient Replicate failures. Missing/failed calls fall back to a mock generator and badge the result.
- TTS issues: Replicate errors fall back to gTTS; gTTS errors fall back to a 2s silent WAV.
- Mux errors (e.g. missing ffmpeg) bubble up with user-facing hints while preserving generated assets when possible.

## Cleanup

Generated audio/video live in temporary files and are cleaned up when the Streamlit session resets or you hit **Clear result**. Review the `PipelineResult.cleanup` helper if you integrate with longer-lived storage.

## Testing locally

- Run `python -m compileall app.py src` to sanity-check syntax.
- Provide a short placeholder mp4 (<30s) to exercise the full flow.
- To simulate fallback states, run without `REPLICATE_API_TOKEN` (mock commentary) or disconnect the network before the TTS stage; gTTS will fall back to local pyttsx3 if available.

## Next steps

- Swap the UI into Next.js + FastAPI when ready for production deployment.
- Replace the mock TTS/LLM fallbacks with richer offline models as needed.
- Integrate light analytics hooks once you have a persist layer.
