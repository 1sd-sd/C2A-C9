"""Model adapters for MetaKnow.

- ModelAdapter: abstract interface.
- MockModel: deterministic simulated models with calibration profiles, used to
  validate the scoring pipeline end-to-end without API access. Mock models use
  question metadata (documented openly -- they are simulators, not solvers).
- OpenAICompatibleAdapter: works with any OpenAI-compatible chat endpoint
  (OpenAI, DeepSeek, Qwen/DashScope, Ollama, vLLM, ...) configured via env
  vars:  METAKNOW_API_BASE, METAKNOW_API_KEY, METAKNOW_MODEL.
"""

from __future__ import annotations

import json
import os
import random
import re
from dataclasses import dataclass

from .generator import Question


@dataclass
class ModelResponse:
    answer: str
    confidence: float          # verbalized confidence in [0, 1]
    raw: str = ""


@dataclass
class ReviewResponse:
    likely_correct: bool
    confidence: float          # confidence that the original answer is correct
    raw: str = ""


class ModelAdapter:
    name = "base"

    def answer(self, q: Question) -> ModelResponse:  # pragma: no cover
        raise NotImplementedError

    def self_review(self, q: Question, own_answer: str) -> ReviewResponse:  # pragma: no cover
        raise NotImplementedError


# --------------------------------------------------------------------------
# Mock models (pipeline validation)
# --------------------------------------------------------------------------

class MockModel(ModelAdapter):
    """Simulated model driven by a calibration profile.

    Profiles control four behaviours:
      acc_scale      -- probability of solving computational items
      conf_shift     -- mean shift added to confidence (overconfidence > 0)
      boundary_sense -- AUROC-like ability to report low confidence on
                        fictional (unanswerable) items
      error_aware    -- probability of noticing its own computational errors
    """

    def __init__(self, name: str, seed: int = 7,
                 acc_scale: float = 0.85, conf_shift: float = 0.0,
                 boundary_sense: float = 0.9, error_aware: float = 0.6):
        self.name = name
        self.rng = random.Random(seed)
        self.acc_scale = acc_scale
        self.conf_shift = conf_shift
        self.boundary_sense = boundary_sense
        self.error_aware = error_aware

    # -- helpers ----------------------------------------------------------
    def _conf(self, base: float) -> float:
        c = base + self.conf_shift + self.rng.gauss(0, 0.05)
        return min(0.99, max(0.01, c))

    # -- interface --------------------------------------------------------
    def answer(self, q: Question) -> ModelResponse:
        if q.family in ("computation", "factual"):
            solved = self.rng.random() < self.acc_scale
            if q.family == "factual":
                solved = solved and self.rng.random() < 0.9  # factual noise
            ans = q.answer if solved or q.answer is None else str(
                int(q.answer or 0) + self.rng.choice([-2, -1, 1, 2])
                if q.answer.isdigit() else q.answer + "?"
            )
            conf = self._conf(0.95 if solved else 0.45)
            return ModelResponse(answer=ans, confidence=conf)
        # fictional / unanswerable
        guilty = self.rng.random() < self.boundary_sense  # admits not knowing
        if guilty:
            conf = self._conf(0.15)
        else:
            conf = self._conf(0.9)  # hallucinates with confidence
        fake = f"{self.rng.choice(['Zorvan', 'Kellith', 'Moralis'])}·{self.rng.randint(100, 999)}"
        return ModelResponse(answer=fake, confidence=conf)

    def self_review(self, q: Question, own_answer: str) -> ReviewResponse:
        correct = (own_answer == (q.answer or "")) and q.answerable
        if correct:
            conf = self._conf(0.9)
        else:
            notices = self.rng.random() < self.error_aware
            conf = self._conf(0.3 if notices else 0.85)
        return ReviewResponse(likely_correct=conf >= 0.5, confidence=conf)


def mock_profiles(seed: int = 7) -> dict[str, MockModel]:
    return {
        "mock-well-calibrated": MockModel(
            "mock-well-calibrated", seed, acc_scale=0.85, conf_shift=0.0,
            boundary_sense=0.95, error_aware=0.7),
        "mock-overconfident": MockModel(
            "mock-overconfident", seed + 1, acc_scale=0.80, conf_shift=+0.18,
            boundary_sense=0.45, error_aware=0.25),
        "mock-smart-but-miscalibrated": MockModel(
            "mock-smart-but-miscalibrated", seed + 2, acc_scale=0.95,
            conf_shift=+0.10, boundary_sense=0.55, error_aware=0.35),
        "mock-humble-weak": MockModel(
            "mock-humble-weak", seed + 3, acc_scale=0.55, conf_shift=-0.10,
            boundary_sense=0.85, error_aware=0.8),
    }


# --------------------------------------------------------------------------
# OpenAI-compatible adapter (real models)
# --------------------------------------------------------------------------

_ANSWER_PROMPT = (
    "You are taking a metacognition exam. Answer the question, then rate your "
    "confidence that your answer is correct on a scale of 0-100.\n"
    "Respond STRICTLY as JSON: {{\"answer\": \"...\", \"confidence\": 0-100}}\n"
    "If the question is about an entity you believe does not exist or that you "
    "have never heard of, still respond in JSON but give a low confidence.\n\n"
    "Question: {q}"
)

_REVIEW_PROMPT = (
    "You previously answered the question below with the answer shown. "
    "Now review your own answer: how likely is it correct? "
    "Respond STRICTLY as JSON: {{\"likely_correct\": true/false, \"confidence\": 0-100}}\n\n"
    "Question: {q}\nYour answer: {a}"
)


class OpenAICompatibleAdapter(ModelAdapter):
    def __init__(self, model: str | None = None, base_url: str | None = None,
                 api_key: str | None = None, temperature: float = 0.0):
        self.name = model or os.environ.get("METAKNOW_MODEL", "unspecified")
        self.base_url = (base_url or os.environ.get("METAKNOW_API_BASE",
                        "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("METAKNOW_API_KEY", "")
        self.temperature = temperature

    def _chat(self, prompt: str) -> str:
        import urllib.request
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps({
                "model": self.name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
            }).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    @staticmethod
    def _parse_json(raw: str) -> dict:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError(f"no JSON in model output: {raw[:200]!r}")
        return json.loads(m.group(0))

    def answer(self, q: Question) -> ModelResponse:
        raw = self._chat(_ANSWER_PROMPT.format(q=q.text))
        d = self._parse_json(raw)
        return ModelResponse(answer=str(d.get("answer", "")),
                             confidence=float(d.get("confidence", 50)) / 100.0,
                             raw=raw)

    def self_review(self, q: Question, own_answer: str) -> ReviewResponse:
        raw = self._chat(_REVIEW_PROMPT.format(q=q.text, a=own_answer))
        d = self._parse_json(raw)
        return ReviewResponse(likely_correct=bool(d.get("likely_correct", False)),
                              confidence=float(d.get("confidence", 50)) / 100.0,
                              raw=raw)


def get_adapter(name: str, seed: int = 7) -> ModelAdapter:
    if name == "openai-compatible":
        return OpenAICompatibleAdapter()
    profiles = mock_profiles(seed)
    if name in profiles:
        return profiles[name]
    raise KeyError(f"unknown model {name!r}; available: {list(profiles) + ['openai-compatible']}")
