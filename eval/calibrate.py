"""기권 임계값 캘리브레이션(AC-5.2) — Conformal Risk Control 방식.

목표: '놓친 레드플래그'(치명 FN)율을 목표 alpha 이하로 통제하는 최소 τ(=최대 coverage)를 라벨셋에서 고른다.
- 방법 = Learn-Then-Test / Conformal Risk Control(BP 인용 [11][12], MAPIE의 CRC와 동일 원리).
  여기선 투명하게 직접 구현 — 데이터가 작아 MAPIE의 통계적 '보장'은 illustrative 수준이라, 원리를
  드러내는 게 더 정직하다. 전체 90+건 실행 시 MAPIE/CRC로 승격 가능.
- 산출: docs/calibration.json (선택 τ, 그때 coverage/FNR) + 콘솔.

★정직 한계: 현재 실측 서브셋 n이 작아 '보장'이 아니라 '경험적 선택'이다. 문서에 명시.
"""
from __future__ import annotations

import json
from pathlib import Path

from metrics import RED, load_results, predict_B

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "calibration.json"


def calibrate(rows: list[dict], alpha: float = 0.0, red_min: int = 2) -> dict:
    """놓친 레드플래그율 <= alpha를 만족하는 최소 τ(최대 coverage)를 찾는다."""
    total_red = sum(1 for r in rows if r["gold"] == RED) or 1
    best = None
    for i in range(0, 21):
        tau = i / 20
        missed = sum(
            1 for r in rows if r["gold"] == RED and predict_B(r, tau, red_min)[0] == "정상"
        )
        fnr = missed / total_red
        abst = sum(1 for r in rows if predict_B(r, tau, red_min)[2])
        cov = (len(rows) - abst) / len(rows)
        if fnr <= alpha:
            # 조건 만족 중 coverage 최대(= τ 최소) 선택
            if best is None or cov > best["coverage"]:
                best = {"tau": round(tau, 2), "fnr": round(fnr, 3), "coverage": round(cov, 3)}
    return best or {"tau": 1.0, "fnr": None, "coverage": 0.0}


def main() -> None:
    rows = load_results()
    result = {
        "method": "Conformal Risk Control (Learn-Then-Test 원리, MAPIE 등가) — 직접 구현",
        "target_alpha_missed_redflag": 0.0,
        "selected": calibrate(rows, alpha=0.0),
        "n": len(rows),
        "caveat": "실측 서브셋 n이 작아 통계적 '보장'이 아닌 경험적 선택. 전체 실행 시 MAPIE/CRC로 승격.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
