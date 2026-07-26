"""라벨 합의 점검(F7) — 독립 2차 모델로 재라벨해 규칙유래 gold와 합의율 측정.

목적: 평가셋 라벨이 '한 모델의 자기확증'이 아님을 보인다(자기확증 회피 defense #2 실행).
- 판정 파이프라인은 claude-sonnet-5. 여기 라벨러는 **다른 모델 claude-haiku-4-5** → 독립.
- 라벨러엔 gold를 주지 않는다(증상·시술·경과일만). 3-way로 독립 분류 → gold와 일치율.
- 합의율이 높으면 규칙유래 라벨을 교차 지지, 낮으면 사람 리뷰 플래그(disagreements 기록).
- 산출: data/eval/consensus.json. 서브셋(기본 15)만 — 비용·시연 목적, 전체는 --limit 0.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CASES = ROOT / "data" / "eval" / "cases.jsonl"
OUT = ROOT / "data" / "eval" / "consensus.json"
LABELER_MODEL = "claude-haiku-4-5-20251001"

SYS = """너는 성형·피부 시술 후 회복 상태를 3분류하는 독립 라벨러다.
정상 / 불확실 / 레드플래그 중 하나로만 답하라(그 단어 하나만 출력, 설명 금지).
- 정상: 경과일에 맞는 흔한 회복.
- 레드플래그: 감염·과출혈·혈관폐색·시야이상 등 응급/이상 신호.
- 불확실: 경계이거나 정보 부족."""


def _key() -> None:
    if os.getenv("ANTHROPIC_API_KEY"):
        return
    v = Path.home() / ".vault" / "enometa-distill" / ".env.local"
    if v.exists():
        m = re.search(r"^ANTHROPIC_API_KEY=(.+)$", v.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip().strip('"').strip("'")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=15)
    args = ap.parse_args()
    _key()
    from anthropic import Anthropic

    client = Anthropic()
    cases = [json.loads(x) for x in CASES.read_text(encoding="utf-8").splitlines() if x.strip()]
    if args.limit:
        cases = cases[:: max(1, len(cases) // args.limit)][: args.limit]  # 균등 샘플

    agree, dis = 0, []
    valid = {"정상", "불확실", "레드플래그"}
    for c in cases:
        u = f"[시술] {c['procedure']} [경과일] {c['days_since']}일\n[증상] {c['symptom_text']}\n3분류:"
        msg = client.messages.create(model=LABELER_MODEL, max_tokens=12, system=SYS,
                                     messages=[{"role": "user", "content": u}])
        raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
        pred = next((v for v in valid if v in raw), "불확실")
        if pred == c["gold_verdict"]:
            agree += 1
        else:
            dis.append({"id": c["id"], "gold": c["gold_verdict"], "independent": pred})
        print(f"  [{c['id']}] gold={c['gold_verdict']} independent={pred} {'✓' if pred==c['gold_verdict'] else '≠'}")

    result = {
        "labeler_model": LABELER_MODEL,
        "judge_model": "claude-sonnet-5 (독립)",
        "n": len(cases),
        "agreement_rate": round(agree / len(cases), 3),
        "note": "규칙유래 gold vs 독립 2차 모델. 완전 자기라벨 아님(defense #2). 불일치는 사람 리뷰 대상.",
        "disagreements": dis,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "disagreements"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
