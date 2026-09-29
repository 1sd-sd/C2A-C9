"""Compute MetaKnow metrics from answers_<model>.json produced by run_real_model.js."""

import json
import sys
import os

# 定位 metaknow 包：优先取环境变量，否则按本文件相对位置自动探测。
# 这样无论从 评测工具/ 还是 lishengdan_C9_benchmark/results/real_models/ 运行都能找到。
_HERE = os.path.dirname(os.path.abspath(__file__))
_CANDIDATES = [
    os.environ.get("METAKNOW_PATH"),
    os.path.join(_HERE, os.pardir, "lishengdan_C9_benchmark"),          # 评测工具/
    os.path.join(_HERE, os.pardir, os.pardir),                          # results/real_models/
    os.path.join(_HERE, os.pardir, os.pardir, "lishengdan_C9_benchmark"),
]
for _p in _CANDIDATES:
    if _p and os.path.isdir(os.path.join(_p, "metaknow")):
        sys.path.insert(0, os.path.abspath(_p))
        break
else:
    sys.exit(
        "找不到 metaknow 包。请设置环境变量 METAKNOW_PATH 指向 lishengdan_C9_benchmark 目录，"
        "或确认该目录与本文件的相对位置未变。"
    )

from metaknow.metrics import (  # noqa: E402
    auroc, brier_score, error_monitoring, expected_calibration_error,
    overconfidence_index, auc_of_risk_coverage, risk_coverage_curve,
)


def normalize(ans):
    if ans is None:
        return ""
    return ans.strip().lower().rstrip(".").replace("，", ",").replace(" ", "")


def grade(item):
    gold = normalize(item.get("gold"))
    got = normalize(item.get("model_answer", ""))
    if not item["answerable"]:
        return 0
    if gold == got:
        return 1
    try:
        return int(abs(float(got) - float(gold)) < 1e-6)
    except ValueError:
        return int(bool(got) and gold in got)


def run(path):
    items = json.load(open(path, encoding="utf-8"))
    for it in items:
        it["correct"] = grade(it)

    s1 = [(it["confidence"], it["correct"]) for it in items
          if it["answerable"] and it.get("self_review_conf") is not None]
    comp = [(it["confidence"], it["correct"], 1) for it in items if it["family"] == "computation"]
    fict = [(it["confidence"], it["correct"], 0) for it in items if it["family"] == "fictional"]
    reviews = [(it["self_review_conf"], it["correct"]) for it in items
               if it.get("self_review_conf") is not None]

    n_err = sum(1 for it in items if it.get("error"))
    acc = sum(y for _, y in s1) / len(s1)
    em = error_monitoring(reviews)
    rc = risk_coverage_curve(comp + fict)

    return {
        "model": os.path.basename(path).replace("answers_", "").replace(".json", ""),
        "n_items": len(items), "n_call_errors": n_err,
        "S1": {
            "accuracy": round(acc, 4),
            "mean_confidence": round(sum(c for c, _ in s1) / len(s1), 4),
            "ECE_10bin": round(expected_calibration_error(s1), 4),
            "Brier": round(brier_score(s1), 4),
            "overconfidence_index": round(overconfidence_index(s1), 4),
        },
        "S2": {
            "AUROC": round(auroc([c for c, _, _ in comp], [c for c, _, _ in fict]), 4),
            "mean_conf_answerable": round(sum(c for c, _, _ in comp) / len(comp), 4),
            "mean_conf_unanswerable": round(sum(c for c, _, _ in fict) / len(fict), 4),
            "risk_coverage_AUC": round(auc_of_risk_coverage(rc), 4),
            "fictional_answered_as_entity_rate": round(
                sum(1 for it in items if it["family"] == "fictional"
                    and normalize(it.get("model_answer", "")) not in ("", "none", "null", "n/a", "不知道", "无"))
                / len(fict), 4),
        },
        "S3": {
            "error_detection_rate": round(em.error_detection_rate, 4),
            "correct_retention_rate": round(em.correct_retention_rate, 4),
            "self_review_AUROC": round(em.self_review_auroc, 4),
            "n_errors": em.n_errors, "n_correct": em.n_corrects,
        },
    }


if __name__ == "__main__":
    out = {}
    for p in sys.argv[1:]:
        r = run(p)
        out[r["model"]] = r
        print(json.dumps(r, ensure_ascii=False, indent=1))
    if len(sys.argv) > 2:
        json.dump(out, open("real_model_reports.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
