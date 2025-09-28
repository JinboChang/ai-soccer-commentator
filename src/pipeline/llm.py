"""LLM integration and fallbacks."""

from __future__ import annotations

import os
import random
import re
from typing import Tuple

from tenacity import retry, stop_after_attempt, wait_exponential

from .constants import REPLICATE_LLM_MODEL, STATUS_MOCK_LLM
from .errors import ExternalServiceError

try:  # pragma: no cover - optional dependency path
    import replicate  # type: ignore
except ImportError:  # pragma: no cover - handled via fallback
    replicate = None  # type: ignore


def _extract_teams(prompt: str) -> Tuple[str, str]:
    match = re.search(r"Teams: (?P<a>.*?) vs (?P<b>.*?).", prompt)
    if not match:
        return ("Team A", "Team B")
    return match.group("a"), match.group("b")


class LLMClient:
    def __init__(
        self,
        *,
        model: str | None = None,
        api_token: str | None = None,
        allow_mock_fallback: bool = True,
        temperature: float = 0.8,
        max_tokens: int = 128,
    ) -> None:
        self.model = model or os.getenv("REPLICATE_LLM_MODEL", REPLICATE_LLM_MODEL)
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        self.allow_mock_fallback = allow_mock_fallback
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, prompt: str, *, language: str) -> Tuple[str, list[str]]:
        notes: list[str] = []
        if not self.api_token or replicate is None:
            commentary = self._mock_response(prompt, language)
            notes.append(STATUS_MOCK_LLM)
            return commentary, notes

        try:
            commentary = self._call_replicate(prompt)
            if not commentary and self.allow_mock_fallback:
                commentary = self._mock_response(prompt, language)
                notes.append(STATUS_MOCK_LLM)
            elif not commentary:
                raise ExternalServiceError(
                    message="LLM returned empty response.",
                    error_code="llm_empty",
                    user_hint="Try again in a few seconds."
                )
            return commentary, notes
        except ExternalServiceError:
            raise
        except Exception as exc:  # pragma: no cover - network edge
            if self.allow_mock_fallback:
                commentary = self._mock_response(prompt, language)
                notes.append(STATUS_MOCK_LLM)
                return commentary, notes
            raise ExternalServiceError(
                message="LLM request failed.",
                error_code="llm_failure",
                user_hint="Please retry shortly."
            ) from exc

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
    def _call_replicate(self, prompt: str) -> str:
        assert replicate is not None  # noqa: S101
        if self.api_token:
            client = replicate.Client(api_token=self.api_token)
            run = client.run
        else:
            run = replicate.run

        output = run(
            self.model,
            input={
                "prompt": prompt,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            },
        )

        if isinstance(output, (list, tuple)):
            text = "".join(str(part) for part in output)
        else:
            text = str(output)
        return text.strip().strip('"')

    def _mock_response(self, prompt: str, language: str) -> str:
        team_a, team_b = _extract_teams(prompt)
        opening_lines = [
            f"{team_a} are flying forward, one-touch football shredding the press and the crowd is on its feet!",
            f"Listen to the roar! {team_b} rip through midfield, a give-and-go opens acres of grass and the box is chaos!",
            f"You can feel the electricity! {team_a} sling a whipped cross in, bodies hurling at the near post!",
        ]
        finishers = [
            "IT'S A STUNNER THAT RATTLES THE TOP BINS!!!",
            "GOAL! SENSATIONAL STRIKE, THE NET IS STILL SHAKING!!!",
            "THE PLACE ERUPTS AS THAT CURLER KISSES THE FAR STANCHION!!!",
            "WHAT A ROCKET, THE KEEPER'S BEATEN ALL ENDS UP!!!",
        ]
        colour_calls = [
            "The touch, the vision, the finish - that's box-office football!",
            "This ground is bouncing, you simply cannot script drama like this!",
            "Championship tempo, heavyweight execution, and the fans are losing their minds!",
        ]
        commentary = f"{random.choice(opening_lines)} {random.choice(finishers)} {random.choice(colour_calls)}"

        if language.startswith("es"):
            commentary = (
                f"{team_a} rompe lineas con puro vértigo, pared y desmarque que enloquecen a la grada! "
                f"GOOOOOOL! {random.choice(['Latigazo inapelable', 'Disparo teledirigido', 'Toque de seda'])} que besa la escuadra y hace temblar el estadio!!!"
            )
        elif language.startswith("ko"):
            commentary = (
                f"{team_a}의 번개 같은 전진입니다! 패스가 번쩍이며 수비를 찢어 놓고 관중의 함성이 폭발합니다! "
                f"마지막 슛이 {random.choice(['골대 상단을 갈라버립니다', '골문 구석으로 빨려 들어갑니다', '스토퍼를 지나며 그물을 뒤흔듭니다'])}!!!"
            )
        return commentary
