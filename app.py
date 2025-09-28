from __future__ import annotations

import streamlit as st

from src.pipeline.constants import (
    DEFAULT_TTS_PROVIDER,
    STATUS_FALLBACK_TTS,
    STATUS_MOCK_LLM,
    STATUS_MOCK_TTS,
    STATUS_TRIMMED_AUDIO,
)
from src.pipeline.errors import ExternalServiceError, MuxingError, PipelineError, ValidationError
from src.pipeline.models import PipelineResult
from src.pipeline.processor import generate_commentated_clip

PAGE_TITLE = "AI Football Commentator"
VIBE_LABELS = {
    "hype": "Hype",
    "calm analysis": "Calm analysis",
    "british pundit": "British pundit",
    "latin radio": "Latin radio",
}
LANGUAGE_OPTIONS = {
    "English (EN)": "en",
    "Spanish (ES)": "es",
    "Korean (KO)": "ko",
}
TTS_PROVIDERS = {
    "Default (gTTS)": "gtts",
    "Replicate TTS": "replicate",
    "Local (pyttsx3)": "pyttsx3",
}

STATUS_LABELS = {
    STATUS_FALLBACK_TTS: "Fallback voice used",
    STATUS_TRIMMED_AUDIO: "Audio trimmed",
    STATUS_MOCK_LLM: "Mock commentary",
    STATUS_MOCK_TTS: "Placeholder audio",
}


def get_session_result() -> PipelineResult | None:
    result = st.session_state.get("pipeline_result")
    if isinstance(result, PipelineResult):
        return result
    return None


def store_session_result(result: PipelineResult) -> None:
    current = get_session_result()
    if current is not None:
        current.cleanup()
    st.session_state["pipeline_result"] = result


def clear_session_result() -> None:
    current = get_session_result()
    if current is not None:
        current.cleanup()
    st.session_state.pop("pipeline_result", None)


st.set_page_config(page_title=PAGE_TITLE, page_icon=":soccer:", layout="wide")
st.title(PAGE_TITLE)
st.caption("Upload a silent soccer clip and generate lively commentary audio in under a minute.")

with st.expander("Usage notice", expanded=False):
    st.markdown(
        "- Upload 10-30 second clips you have rights to share.\n"
        "- Commentary stays family-friendly by design.\n"
        "- Processing happens on this machine; API keys stay server-side."
    )

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    upload = st.file_uploader(
        "Upload your silent soccer clip",
        type=["mp4", "mov", "webm"],
        accept_multiple_files=False,
        help="Clips must be 10-30 seconds and under 60MB.",
    )

with col_right:
    selected_vibe_label = st.selectbox(
        "Commentary vibe",
        list(VIBE_LABELS.values()),
        index=0,
    )
    vibe_key = next(key for key, label in VIBE_LABELS.items() if label == selected_vibe_label)

    team_a = st.text_input("Team A", placeholder="Team A")
    team_b = st.text_input("Team B", placeholder="Team B")
    key_moments = st.text_area("Key moments", placeholder="Fast counter, curled finish")

with st.expander("Advanced options"):
    language_label = st.selectbox("Commentary language", list(LANGUAGE_OPTIONS.keys()), index=0)
    language_code = LANGUAGE_OPTIONS[language_label]

    provider_label = st.selectbox(
        "TTS provider",
        list(TTS_PROVIDERS.keys()),
        index=list(TTS_PROVIDERS.values()).index(DEFAULT_TTS_PROVIDER),
        help="Replicate voices require a configured model and API token.",
    )
    tts_provider = TTS_PROVIDERS[provider_label]

trigger = st.button("Generate commentary", type="primary")

if trigger:
    clear_session_result()
    if upload is None:
        st.warning("Please upload a clip before generating commentary.")
    else:
        try:
            with st.spinner("Building commentary..."):
                video_bytes = upload.getvalue()
                result = generate_commentated_clip(
                    video_bytes=video_bytes,
                    filename=upload.name,
                    vibe=vibe_key,
                    team_a=team_a,
                    team_b=team_b,
                    key_moments=key_moments,
                    language=language_code,
                    tts_provider=tts_provider,
                )
            store_session_result(result)
            st.success("Commentary ready! Scroll down to preview and download.")
        except ValidationError as exc:
            st.error(f"{exc.message}\n\nHint: {exc.user_hint}")
        except ExternalServiceError as exc:
            st.error(f"{exc.message}\n\nHint: {exc.user_hint}")
        except MuxingError as exc:
            st.error(f"{exc.message}\n\nHint: {exc.user_hint}")
        except PipelineError as exc:
            st.error(f"{exc.message}\n\nHint: {exc.user_hint}")

st.divider()

result = get_session_result()
if result is not None:
    st.subheader("Commentary preview")
    st.write(result.commentary_text)

    if result.status_notes:
        st.caption("Status")
        note_cols = st.columns(len(result.status_notes))
        for idx, note in enumerate(result.status_notes):
            label = STATUS_LABELS.get(note, note)
            note_cols[idx].success(label)

    st.markdown("### Audio preview")
    with result.audio_path.open("rb") as audio_file:
        audio_bytes = audio_file.read()
        mime = "audio/wav" if result.audio_path.suffix == ".wav" else "audio/mpeg"
        st.audio(audio_bytes, format=mime)

    st.markdown("### Video preview")
    with result.video_path.open("rb") as video_file:
        video_bytes = video_file.read()
        st.video(video_bytes)

    st.download_button(
        "Download MP4",
        data=video_bytes,
        file_name="commentated_clip.mp4",
        mime="video/mp4",
        use_container_width=True,
    )

    st.download_button(
        "Download audio only",
        data=audio_bytes,
        file_name="commentary_audio.wav" if result.audio_path.suffix == ".wav" else "commentary_audio.mp3",
        mime=mime,
        use_container_width=True,
    )

    if st.button("Clear result"):
        clear_session_result()
        st.experimental_rerun()
