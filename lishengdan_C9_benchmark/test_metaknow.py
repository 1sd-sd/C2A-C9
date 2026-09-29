"""Sanity tests for MetaKnow metrics. Run: python test_metaknow.py"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metaknow.generator import build_paper, gen_fictional
import random
from metaknow.metrics import (
    auroc, brier_score, expected_calibration_error, overconfidence_index,
    error_monitoring, risk_coverage_curve, auc_of_risk_coverage,
)

failures = []


def check(name, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
    if not cond:
        failures.append(name)


# --- generator integrity ---
paper = build_paper(seed=42, n_computation=20, n_factual=10, n_fictional=20)
check("paper size", len(paper) == 50, str(len(paper)))
check("unique qids", len({q.qid for q in paper}) == 50)
comp = [q for q in paper if q.family == "computation"]
fict = [q for q in paper if q.family == "fictional"]
check("computation answerable", all(q.answerable and q.answer for q in comp))
check("fictional unanswerable", all(not q.answerable and q.answer is None for q in fict))
check("fictional has no real-fragment leak", all(
    not any(frag in q.text.lower() for frag in ["stan ", "germ", "japa"]) for q in fict))
check("paper deterministic (same seed)",
      [q.text for q in build_paper(seed=7, n_computation=5, n_factual=5, n_fictional=5)]
      == [q.text for q in build_paper(seed=7, n_computation=5, n_factual=5, n_fictional=5)])
check("paper differs across seeds",
      [q.text for q in build_paper(seed=7, n_computation=5, n_factual=5, n_fictional=5)]
      != [q.text for q in build_paper(seed=8, n_computation=5, n_factual=5, n_fictional=5)])

# --- metrics: known-answer cases ---
check("AUROC perfect separation", auroc([0.9, 0.8], [0.2, 0.1]) == 1.0)
check("AUROC chance level", abs(auroc([0.5, 0.5], [0.5, 0.5]) - 0.5) < 1e-9)
check("AUROC reversed", auroc([0.1, 0.2], [0.8, 0.9]) == 0.0)
check("Brier perfect", brier_score([(1.0, 1), (0.0, 0)]) == 0.0)
check("Brier worst", brier_score([(1.0, 0), (0.0, 1)]) == 1.0)
check("ECE perfectly calibrated", expected_calibration_error(
    [(0.7, 1)] * 7 + [(0.7, 0)] * 3) < 1e-9)
check("overconfidence sign", overconfidence_index([(0.9, 0), (0.9, 0)]) == 0.9)
em = error_monitoring([(0.2, 0), (0.3, 0), (0.9, 1), (0.8, 1), (0.9, 1)])
check("error detection rate", abs(em.error_detection_rate - 1.0) < 1e-9, str(em.error_detection_rate))
check("correct retention rate", abs(em.correct_retention_rate - 1.0) < 1e-9)
check("review AUROC perfect", em.self_review_auroc == 1.0)
curve = risk_coverage_curve([(0.9, 1, 1), (0.8, 1, 1), (0.2, 0, 0), (0.1, 0, 0)])
check("risk-coverage monotone non-decreasing", all(
    curve[i][1] <= curve[i + 1][1] + 1e-9 for i in range(len(curve) - 1)))
# Unanswerable items set the floor: covering all N items with 1 unanswerable
# of 3 gives risk 1/3 at full coverage -> AUC = trapz = 1/18, NOT zero.
# A badly-inverted confidence ordering (unanswerable ranked highest) must
# produce a strictly worse AUC. (Note: re-sorting a permutation gives the
# same curve, so the "worse" case must use genuinely inverted scores.)
perfect = risk_coverage_curve([(1.0, 1, 1), (0.9, 1, 1), (0.1, 0, 0)])
inverted = risk_coverage_curve([(1.0, 0, 0), (0.5, 1, 1), (0.4, 1, 1)])
check("risk-coverage AUC equals analytic floor 1/18",
      abs(auc_of_risk_coverage(perfect) - 1 / 18) < 1e-9,
      f"{auc_of_risk_coverage(perfect):.4f}")
check("risk-coverage perfect < inverted", auc_of_risk_coverage(perfect) < auc_of_risk_coverage(inverted))

# --- mock adapter behaviour ---
from metaknow.adapters import mock_profiles
prof = mock_profiles(seed=7)
good, bad = prof["mock-well-calibrated"], prof["mock-overconfident"]
rng = random.Random(0)
fict_items = gen_fictional(rng, 30)
gc = [good.answer(q).confidence for q in fict_items]
bc = [bad.answer(q).confidence for q in fict_items]
check("calibrated mock low-conf on fiction", sum(gc) / len(gc) < 0.35, f"mean={sum(gc)/len(gc):.2f}")
check("overconfident mock high-conf on fiction", sum(bc) / len(bc) > 0.5, f"mean={sum(bc)/len(bc):.2f}")

print()
print("ALL PASS" if not failures else f"{len(failures)} FAILURES: {failures}")
sys.exit(0 if not failures else 1)
