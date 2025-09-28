"""Prompt construction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

from .constants import DEFAULT_LANGUAGE, VIBE_PROMPTS


@dataclass
class PromptContext:
    prompt: str
    language: str
    vibe_key: str


def normalise_vibe(vibe: str) -> str:
    vibe_key = (vibe or "").strip().lower()
    if vibe_key not in VIBE_PROMPTS:
        return "hype"
    return vibe_key


def _render_team_block(team_a: str | None, team_b: str | None) -> str:
    name_a = (team_a or "Team A").strip() or "Team A"
    name_b = (team_b or "Team B").strip() or "Team B"
    return f"Teams: {name_a} vs {name_b}."


def _render_key_moments_block(key_moments: str | None) -> str:
    value = (key_moments or "None").strip() or "None"
    return f"Key moments: {value}."


def build_prompt(
    *,
    vibe: str,
    team_a: str | None,
    team_b: str | None,
    key_moments: str | None,
    language: str | None,
) -> PromptContext:
    vibe_key = normalise_vibe(vibe)
    language_code = (language or DEFAULT_LANGUAGE).strip().lower() or DEFAULT_LANGUAGE

    prompt = dedent(
        f"""
        SYSTEM: You are a live football commentator delivering a broadcast call. Paint the picture with elite-match jargon
        (edge of the box, whipped cross, top bins, box-to-box, counter-press), weave in crowd reaction, and keep it family-friendly.
        Use two or three punchy sentences that mix short bursts with longer build-ups, include at least two exclamation points, and
        make the decisive moment feel seismic. Do not mention 'video' or 'silence'.

        VIBE: {VIBE_PROMPTS[vibe_key]}

        CONTEXT:
        {_render_team_block(team_a, team_b)}
        {_render_key_moments_block(key_moments)}
        Language: {language_code}.

        Now generate the commentary.
        """
    ).strip()

    return PromptContext(prompt=prompt, language=language_code, vibe_key=vibe_key)
