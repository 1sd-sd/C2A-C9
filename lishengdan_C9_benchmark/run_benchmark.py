#!/usr/bin/env python3
"""Run the MetaKnow benchmark.

Usage:
  python run_benchmark.py --model mock-well-calibrated [--seed 42] [--out results/]
  python run_benchmark.py --model openai-compatible --n-comp 40 --n-fict 40

With no API key configured, use the built-in mock profiles to validate the
pipeline (documented as simulation, not real model performance).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metaknow.adapters import get_adapter
from metaknow.generator import build_paper
from metaknow.metrics import (
    auroc, brier_score, error_monitoring, expected_calibration_error,
    overconfidence_index, auc_of_risk_coverage, risk_coverage_curve,
)


def normalize(ans: str | None) -> str:
    if ans is None:
        return ""
    return ans.strip().lower().rstrip(".").replace("，", ",").replace(" ", "")


def grade(resp_answer: str, q) -> int:
    if not q.answerable:
        return 0  # answering an unanswerable item is always wrong
    gold = normalize(q.answer)
    got = normalize(resp_answer)
    if gold == got:
        return 1
    # numeric tolerance for arithmetic items
    if q.family == "computation":
        try:
            return int(abs(float(got) - float(gold)) < 1e-6)
        except ValueError:
            return 0
    # substring credit for short factual answers
    return int(bool(got) and gold in got)


def run(model_name: str, seed: int, n_comp: int, n_fact: int, n_fict: int,
        out_dir: str) -> dict:
    adapter = get_adapter(model_name, seed=seed)
    paper = build_paper(seed=seed, n_computation=n_comp, n_factual=n_fact,
                        n_fictional=n_fict)

    s1_pairs, s2_answerable_conf, s2_unanswerable_conf, rc_items = [], [], [], []
    reviews, log = [], []

    t0 = time.time()
    for q in paper:
        r = adapter.answer(q)
        correct = grade(r.answer, q)
        conf = r.confidence
        log.append({"qid": q.qid, "family": q.family, "answerable": q.answerable,
                    "text": q.text, "gold": q.answer, "model_answer": r.answer,
                    "confidence": round(conf, 4), "correct": correct})

        if "S1" in q.metadata["phase"] and q.answerable:
            s1_pairs.append((conf, correct))
        if q.family == "computation":          # S2 answerable component
            s2_answerable_conf.append(conf)
            rc_items.append((conf, correct, 1))
        if q.family == "fictional":            # S2 unanswerable component
            s2_unanswerable_conf.append(conf)
            rc_items.append((conf, correct, 0))
        if "S1" in q.metadata["phase"] and q.answerable:
            rev = adapter.self_review(q, r.answer)
            reviews.append((rev.confidence, correct))
            log[-1]["self_review_conf"] = round(rev.confidence, 4)

    elapsed = time.time() - t0

    s1_acc = sum(y for _, y in s1_pairs) / len(s1_pairs)
    em = error_monitoring(reviews)
    rc_curve = risk_coverage_curve(rc_items)

    report = {
        "model": adapter.name,
        "seed": seed,
        "n_items": len(paper),
        "wall_time_sec": round(elapsed, 1),
        "S1_confidence_calibration": {
            "accuracy": round(s1_acc, 4),
            "mean_confidence": round(sum(c for c, _ in s1_pairs) / len(s1_pairs), 4),
            "ECE_10bin": round(expected_calibration_error(s1_pairs), 4),
            "Brier": round(brier_score(s1_pairs), 4),
            "overconfidence_index": round(overconfidence_index(s1_pairs), 4),
        },
        "S2_boundary_awareness": {
            "AUROC_answerable_vs_fictional": round(
                auroc(s2_answerable_conf, s2_unanswerable_conf), 4),
            "mean_conf_on_answerable": round(sum(s2_answerable_conf) / len(s2_answerable_conf), 4),
            "mean_conf_on_unanswerable": round(sum(s2_unanswerable_conf) / len(s2_unanswerable_conf), 4),
            "risk_coverage_AUC_lower_better": round(auc_of_risk_coverage(rc_curve), 4),
        },
        "S3_error_monitoring": {
            "error_detection_rate": round(em.error_detection_rate, 4),
            "correct_retention_rate": round(em.correct_retention_rate, 4),
            "self_review_AUROC": round(em.self_review_auroc, 4),
            "n_errors": em.n_errors, "n_correct": em.n_corrects,
        },
    }

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, f"metaknow_{model_name}_seed{seed}.json"),
              "w", encoding="utf-8") as f:
        json.dump({"report": report, "items": log}, f, ensure_ascii=False, indent=2)

    with open(os.path.join(out_dir, f"metaknow_{model_name}_seed{seed}_rc_curve.csv"),
              "w", encoding="utf-8") as f:
        f.write("coverage,risk\n")
        for cov, risk in rc_curve:
            f.write(f"{cov:.4f},{risk:.4f}\n")

    return report


def main() -> None:
    p = argparse.ArgumentParser(description="MetaKnow metacognition benchmark")
    p.add_argument("--model", default="mock-well-calibrated",
                   help="mock-well-calibrated | mock-overconfident | "
                        "mock-smart-but-miscalibrated | mock-humble-weak | "
                        "openai-compatible")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n-comp", type=int, default=60)
    p.add_argument("--n-fact", type=int, default=30)
    p.add_argument("--n-fict", type=int, default=60)
    p.add_argument("--out", default="results")
    a = p.parse_args()

    report = run(a.model, a.seed, a.n_comp, a.n_fact, a.n_fict, a.out)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
