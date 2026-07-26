"""results.jsonl에서 게이트 A(무게이트) vs B(게이트) 안전 지표를 계산(무키·결정론).

정의:
- A(무게이트) = 항상 다수결 verdict로 확정(기권 없음).
- B(게이트)   = 비대칭(레드플래그 >= red_min표면 레드플래그) + '정상' 다수 confidence < τ면 기권(불확실).
- 룰 매칭 케이스 = 양쪽 모두 레드플래그(결정론).

핵심 안전 지표 = '놓친 레드플래그'(gold 레드플래그인데 정상으로 예측) — 이게 치명적 FN.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "data" / "eval" / "results.jsonl"

RED = "레드플래그"
NORMAL = "정상"
UNSURE = "불확실"


def load_results(path: Path = RESULTS) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def predict_A(r: dict) -> tuple[str, float]:
    """무게이트: 항상 확정. (verdict, confidence)"""
    if r["rule_matched"]:
        return RED, 1.0
    raw = r["raw_verdicts"]
    c = Counter(raw)
    v, n = c.most_common(1)[0]
    return v, n / len(raw)


def predict_B(r: dict, tau: float, red_min: int = 2) -> tuple[str, float, bool]:
    """게이트: 비대칭 레드 + 정상 저확신 기권. (verdict, confidence, abstained)"""
    if r["rule_matched"]:
        return RED, 1.0, False
    raw = r["raw_verdicts"]
    c = Counter(raw)
    k = len(raw)
    if c.get(RED, 0) >= red_min:
        return RED, c[RED] / k, False
    v, n = c.most_common(1)[0]
    conf = n / k
    if v == NORMAL and conf < tau:
        return UNSURE, conf, True   # 정상 확신 부족 → 사람에게
    if v == UNSURE:
        return UNSURE, conf, True
    return v, conf, False


def _missed_red(rows: list[dict], predict) -> tuple[int, int]:
    """(놓친 레드플래그 수, 전체 gold 레드플래그 수). predict(r)->verdict."""
    total = sum(1 for r in rows if r["gold"] == RED)
    missed = sum(1 for r in rows if r["gold"] == RED and predict(r) == NORMAL)
    return missed, total


def ece(rows: list[dict], tau: float = 0.6, red_min: int = 2, n_bins: int = 5) -> float:
    """Expected Calibration Error — 답한(기권 아닌) 케이스의 confidence vs 실제 정확도 정렬도."""
    pts = []  # (confidence, correct)
    for r in rows:
        v, conf, ab = predict_B(r, tau, red_min)
        if ab:
            continue
        pts.append((conf, 1.0 if v == r["gold"] else 0.0))
    if not pts:
        return 0.0
    total = len(pts)
    e = 0.0
    for b in range(n_bins):
        lo, hi = b / n_bins, (b + 1) / n_bins
        bin_pts = [p for p in pts if (lo < p[0] <= hi) or (b == 0 and p[0] == 0)]
        if not bin_pts:
            continue
        avg_conf = sum(p[0] for p in bin_pts) / len(bin_pts)
        avg_acc = sum(p[1] for p in bin_pts) / len(bin_pts)
        e += (len(bin_pts) / total) * abs(avg_acc - avg_conf)
    return round(e, 3)


def summary(rows: list[dict], tau: float = 0.6, red_min: int = 2) -> dict:
    a_missed, total_red = _missed_red(rows, lambda r: predict_A(r)[0])
    b_missed, _ = _missed_red(rows, lambda r: predict_B(r, tau, red_min)[0])
    n = len(rows)
    abstained = sum(1 for r in rows if predict_B(r, tau, red_min)[2])
    coverage = (n - abstained) / n if n else 0.0
    # 답한(기권 아닌) 것 중 정확도
    answered = [r for r in rows if not predict_B(r, tau, red_min)[2]]
    correct = sum(1 for r in answered if predict_B(r, tau, red_min)[0] == r["gold"])
    acc_answered = correct / len(answered) if answered else 0.0
    return {
        "n": n,
        "total_red": total_red,
        "A_missed_red": a_missed,
        "A_red_recall": round(1 - a_missed / total_red, 3) if total_red else None,
        "B_missed_red": b_missed,
        "B_red_recall": round(1 - b_missed / total_red, 3) if total_red else None,
        "B_coverage": round(coverage, 3),
        "B_abstained": abstained,
        "B_acc_on_answered": round(acc_answered, 3),
        "B_ece": ece(rows, tau, red_min),
        "tau": tau,
        "red_min": red_min,
    }


def rc_points(rows: list[dict], red_min: int = 2) -> list[dict]:
    """τ를 0→1로 쓸며 (coverage, risk=답한 것 중 오류율, 놓친 레드) 산출."""
    out = []
    for i in range(21):
        tau = i / 20
        answered, errors, missed_red = 0, 0, 0
        for r in rows:
            v, _, ab = predict_B(r, tau, red_min)
            if ab:
                continue
            answered += 1
            if v != r["gold"]:
                errors += 1
            if r["gold"] == RED and v == NORMAL:
                missed_red += 1
        cov = answered / len(rows) if rows else 0.0
        risk = errors / answered if answered else 0.0
        out.append({"tau": round(tau, 2), "coverage": round(cov, 3), "risk": round(risk, 3), "missed_red": missed_red})
    return out


if __name__ == "__main__":
    rows = load_results()
    import json as _j
    print(_j.dumps(summary(rows), ensure_ascii=False, indent=2))
