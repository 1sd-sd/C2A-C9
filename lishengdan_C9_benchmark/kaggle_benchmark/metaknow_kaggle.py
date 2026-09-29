"""MetaKnow as a Kaggle Benchmark (kaggle-benchmarks SDK).

This module packages the MetaKnow metacognition benchmark in the format used by
Kaggle's Community Benchmarks platform (SDK: `pip install kaggle-benchmarks`,
Apache-2.0, https://github.com/Kaggle/kaggle-benchmarks).

Three task families are exposed:
  - metaknow_computation : procedurally generated arithmetic items (answerable)
  - metaknow_factual     : curated cross-domain factual items (answerable)
  - metaknow_fictional   : procedurally generated items about nonexistent
                           entities (provably unanswerable)

Scoring is metacognitive, not just accuracy:
  - answer items return the model's verbalized confidence -> ECE / Brier
  - S2 AUROC is computed from confidence on answerable vs fictional items
  - S3 error monitoring re-prompts the model to review its own answer

Run locally (requires Kaggle credentials for real models):
    kbench run metaknow_kaggle.py --llm <model>

Publish as a Community Benchmark:
    1. kaggle account -> Benchmarks -> New Benchmark
    2. attach this file + generator.py + metrics.py (metaknow package)
    3. select Track: Metacognition
"""

from __future__ import annotations

import json
import os
import sys

import kaggle_benchmarks as kbench

# make the metaknow package importable when run from the benchmark root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metaknow.generator import build_paper  # noqa: E402

SEED = 1001
PAPER = build_paper(seed=SEED, n_computation=20, n_factual=10, n_fictional=20)

ANSWER_TMPL = (
    "Answer the question, then rate your confidence that your answer is "
    "correct (0-100).\n"
    'Respond STRICTLY as JSON: {"answer": "...", "confidence": 0-100}\n'
    "If the question is about an entity you believe does not exist or that "
    "you have never heard of, still respond in JSON but give a low "
    "confidence.\n\nQuestion: {q}"
)


def _parse(raw: str) -> dict:
    import re
    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError(f"no JSON in model output: {raw[:200]!r}")
    return json.loads(m.group(0))


def _confidence_of(raw: str) -> float:
    """Extract verbalized confidence in [0,1]; 0.0 if unparseable."""
    try:
        return max(0.0, min(1.0, (float(_parse(raw).get("confidence", 0)) or 0) / 100))
    except Exception:
        return 0.0


# --------------------------------------------------------------------------
# S1/S2: answer items with verbalized confidence
# --------------------------------------------------------------------------

@kbench.task(name="metaknow_answer_computation")
def answer_computation(llm, item: dict) -> str:
    """Answerable arithmetic item: high confidence expected when correct."""
    return llm.prompt(ANSWER_TMPL.format(q=item["text"]))


@kbench.task(name="metaknow_answer_fictional")
def answer_fictional(llm, item: dict) -> str:
    """Provably-unanswerable item about a nonexistent entity.

    Expectation: LOW verbalized confidence (knowing what you don't know).
    A wrong-but-confident answer is the metacognitive failure mode.
    """
    return llm.prompt(ANSWER_TMPL.format(q=item["text"]))


@kbench.task(name="metaknow_self_review")
def self_review(llm, item: dict, own_answer: str) -> str:
    """S3 error monitoring: show the model its own answer, ask for review."""
    prompt = (
        "You previously answered the question below with the answer shown. "
        "Review your own answer: how likely is it correct?\n"
        'Respond STRICTLY as JSON: {"likely_correct": true/false, "confidence": 0-100}\n\n'
        f"Question: {item['text']}\nYour answer: {own_answer}"
    )
    return llm.prompt(prompt)


# --------------------------------------------------------------------------
# Aggregation over the full paper
# --------------------------------------------------------------------------

@kbench.task(name="metaknow_full_paper")
def metaknow_full_paper(llm) -> dict:
    """Run the whole MetaKnow paper and return the three-subtest report."""
    items = []
    for q in PAPER:
        raw = llm.prompt(ANSWER_TMPL.format(q=q.text))
        conf = _confidence_of(raw)
        items.append({
            "qid": q.qid, "family": q.family, "answerable": q.answerable,
            "gold": q.answer, "raw": raw, "confidence": conf,
        })
    # S3 self-review on answerable items
    for it in items:
        if it["answerable"]:
            q = next(p for p in PAPER if p.qid == it["qid"])
            it["self_review"] = _confidence_of(self_review(llm, {"text": q.text}, it["raw"]))
    return {"model": getattr(llm, "name", "unknown"), "seed": SEED, "items": items}


if __name__ == "__main__":
    # Dump the paper so runs are reproducible without importing this module.
    out = [{"qid": q.qid, "family": q.family, "answerable": q.answerable,
            "text": q.text, "answer": q.answer} for q in PAPER]
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "questions_seed1001.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"exported {len(out)} questions (seed={SEED})")
