"""Scoring metrics for MetaKnow. Pure standard library."""

from __future__ import annotations

import math
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# Calibration metrics (S1)
# --------------------------------------------------------------------------

def brier_score(pairs: list[tuple[float, int]]) -> float:
    """Mean (confidence - correct)^2. pairs = [(confidence, is_correct)]."""
    if not pairs:
        return float("nan")
    return sum((c - y) ** 2 for c, y in pairs) / len(pairs)


def expected_calibration_error(pairs: list[tuple[float, int]],
                               n_bins: int = 10) -> float:
    """Standard 10-bin ECE (Naeini et al., 2015)."""
    if not pairs:
        return float("nan")
    bin_total = [0] * n_bins
    bin_correct = [0.0] * n_bins
    bin_conf = [0.0] * n_bins
    for conf, correct in pairs:
        b = min(n_bins - 1, int(conf * n_bins))
        bin_total[b] += 1
        bin_correct[b] += correct
        bin_conf[b] += conf
    ece = 0.0
    n = len(pairs)
    for b in range(n_bins):
        if bin_total[b] == 0:
            continue
        acc = bin_correct[b] / bin_total[b]
        avg_conf = bin_conf[b] / bin_total[b]
        ece += (bin_total[b] / n) * abs(acc - avg_conf)
    return ece


def overconfidence_index(pairs: list[tuple[float, int]]) -> float:
    """mean(confidence) - accuracy. Positive = overconfident."""
    if not pairs:
        return float("nan")
    n = len(pairs)
    return sum(c for c, _ in pairs) / n - sum(y for _, y in pairs) / n


# --------------------------------------------------------------------------
# Discrimination metric (S2): AUROC of confidence for answerable vs not
# --------------------------------------------------------------------------

def auroc(scores_pos: list[float], scores_neg: list[float]) -> float:
    """Rank-based AUROC (Mann-Whitney U). pos should score HIGHER."""
    if not scores_pos or not scores_neg:
        return float("nan")
    all_scores = [(s, 1) for s in scores_pos] + [(s, 0) for s in scores_neg]
    all_scores.sort(key=lambda t: t[0])
    # average ranks handle ties
    ranks = [0.0] * len(all_scores)
    i = 0
    while i < len(all_scores):
        j = i
        while j + 1 < len(all_scores) and all_scores[j + 1][0] == all_scores[i][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    rank_sum_pos = sum(r for r, (_, lab) in zip(ranks, all_scores) if lab == 1)
    n_pos, n_neg = len(scores_pos), len(scores_neg)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2
    return u / (n_pos * n_neg)


# --------------------------------------------------------------------------
# Error monitoring (S3)
# --------------------------------------------------------------------------

@dataclass
class ErrorMonitoringResult:
    error_detection_rate: float   # P(self says wrong | actually wrong)
    correct_retention_rate: float # P(self says correct | actually correct)
    n_errors: int
    n_corrects: int
    self_review_auroc: float      # AUROC of review confidence vs correctness


def error_monitoring(reviews: list[tuple[float, int]]) -> ErrorMonitoringResult:
    """reviews = [(review_confidence_that_own_answer_is_correct, actually_correct)]."""
    wrong = [(c, y) for c, y in reviews if y == 0]
    right = [(c, y) for c, y in reviews if y == 1]
    edr = (sum(1 for c, _ in wrong if c < 0.5) / len(wrong)) if wrong else float("nan")
    crr = (sum(1 for c, _ in right if c >= 0.5) / len(right)) if right else float("nan")
    auc = auroc([c for c, y in right], [c for c, y in wrong])
    return ErrorMonitoringResult(edr, crr, len(wrong), len(right), auc)


# --------------------------------------------------------------------------
# Selective prediction (S2 auxiliary)
# --------------------------------------------------------------------------

def risk_coverage_curve(items: list[tuple[float, int, int]]) -> list[tuple[float, float]]:
    """items = [(confidence, is_correct, is_answerable)].
    Returns [(coverage, risk)] when deferring low-confidence items, where
    answering an unanswerable item always counts as incorrect."""
    ordered = sorted(items, key=lambda t: -t[0])
    curve = []
    n = len(ordered)
    correct = 0
    for k, (conf, y, ans) in enumerate(ordered, 1):
        if ans == 1:
            correct += y
        curve.append((k / n, 1 - correct / k))
    return curve


def auc_of_risk_coverage(curve: list[tuple[float, float]]) -> float:
    """Lower is better. 0 = perfect selective predictor."""
    if not curve:
        return float("nan")
    s = 0.0
    prev_x, prev_y = 0.0, 0.0
    for x, y in curve:
        s += (x - prev_x) * (y + prev_y) / 2
        prev_x, prev_y = x, y
    return s
