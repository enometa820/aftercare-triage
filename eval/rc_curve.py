"""Risk-Coverage 곡선 + 게이트 A/B 비교 시각화(AC-9). 무키·결정론(results.jsonl 소비).

산출: docs/measured-safety.png + docs/metrics.json.
축 라벨은 matplotlib 한글 폰트 이슈를 피해 영문으로 둔다(내용은 한국어 리포트에서 설명).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from metrics import load_results, predict_A, rc_points, summary  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "docs" / "measured-safety.png"
OUT_JSON = ROOT / "docs" / "metrics.json"


def main() -> None:
    rows = load_results()
    pts = rc_points(rows)
    summ = summary(rows)

    covs = [p["coverage"] for p in pts]
    risks = [p["risk"] for p in pts]

    # A(무게이트) 지점 = 전부 답함(coverage 1.0), 그때의 오류율.
    a_err = sum(1 for r in rows if predict_A(r)[0] != r["gold"]) / len(rows)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    # 좌: Risk-Coverage 곡선 (B, τ 스윕) + A 지점.
    ax1.plot(covs, risks, "-o", ms=3, label="B: gated (sweep tau)")
    ax1.scatter([1.0], [a_err], c="crimson", zorder=5, label=f"A: no gate (cov=1.0, risk={a_err:.2f})")
    ax1.set_xlabel("Coverage (fraction answered)")
    ax1.set_ylabel("Risk (error rate on answered)")
    ax1.set_title("Risk-Coverage: gate defers low-confidence cases")
    ax1.grid(alpha=0.3)
    ax1.legend(fontsize=8)

    # 우: 놓친 레드플래그(치명 FN) A vs B.
    labels = ["A: no gate", f"B: gate (tau={summ['tau']})"]
    missed = [summ["A_missed_red"], summ["B_missed_red"]]
    bars = ax2.bar(labels, missed, color=["crimson", "steelblue"])
    ax2.set_ylabel("Missed red-flags (gold=RED predicted NORMAL)")
    ax2.set_title(f"Missed red-flags  (total red={summ['total_red']}, n={summ['n']})")
    ax2.bar_label(bars)
    ax2.set_ylim(0, max(3, max(missed) + 1))

    fig.suptitle("Sonar Care — Measured Safety (real Claude run, synthetic labeled subset)", fontsize=11)
    fig.tight_layout()
    OUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PNG, dpi=130)

    OUT_JSON.write_text(
        json.dumps({"summary": summ, "A_error_rate": round(a_err, 3), "rc_points": pts}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"saved {OUT_PNG.name}, {OUT_JSON.name}")
    print(json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
