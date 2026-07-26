"""평가셋을 실 파이프라인에 돌려 per-case 결과를 data/eval/results.jsonl에 캐시.

- 여기서만 실 Claude를 호출한다(키 필요). 산출된 results.jsonl은 이후 test·rc_curve·calibrate가
  '무키·결정론'으로 소비 → CI/재현이 API 없이 돈다.
- per-case로 raw k-sample verdict를 저장해, 나중에 게이트 A(무게이트)/B(게이트) 둘 다 이 raw에서 계산.
- 증분: 이미 results에 있는 id는 건너뜀. 층화 서브셋(--limit N 시 시술×클래스 균형).
- 키는 env 우선, 없으면 vault(enometa-distill/.env.local)에서 로드. 값 출력 0.

사용:
    .venv/Scripts/python.exe eval/run_eval.py --k 5 --limit 18   # 데모 서브셋
    .venv/Scripts/python.exe eval/run_eval.py --k 5              # 전체 90건
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

CASES = ROOT / "data" / "eval" / "cases.jsonl"
RESULTS = ROOT / "data" / "eval" / "results.jsonl"


def _ensure_key() -> None:
    if os.getenv("ANTHROPIC_API_KEY"):
        return
    vault = Path.home() / ".vault" / "enometa-distill" / ".env.local"
    if vault.exists():
        m = re.search(r"^ANTHROPIC_API_KEY=(.+)$", vault.read_text(encoding="utf-8"), re.M)
        if m:
            os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip().strip('"').strip("'")


def _load_cases() -> list[dict]:
    return [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stratify(cases: list[dict], limit: int) -> list[dict]:
    """시술×클래스 균형으로 limit건 추림(경계 우선)."""
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for c in cases:
        buckets[(c["procedure"], c["gold_verdict"])].append(c)
    for b in buckets.values():
        b.sort(key=lambda c: not c.get("boundary", False))  # boundary=True 먼저
    per = max(1, limit // max(1, len(buckets)))
    out: list[dict] = []
    for b in buckets.values():
        out.extend(b[:per])
    return out[:limit]


def _run_case(case: dict, k: int) -> dict:
    from sonar_care.judge import judge_once
    from sonar_care.kb import route_kb
    from sonar_care.redflags import match_redflags
    from sonar_care.schema import Language, PatientInput, Procedure

    inp = PatientInput(
        symptom_text=case["symptom_text"],
        procedure=Procedure(case["procedure"]),
        days_since=case["days_since"],
        language=Language(case["language"]),
    )
    matched = match_redflags(inp.symptom_text, inp.language, inp.procedure)
    raw: list[str] = []
    if not matched:
        kb_context, kb_ids = route_kb(inp.procedure, inp.days_since)
        for _ in range(k):
            raw.append(judge_once(inp, kb_context, kb_ids).verdict.value)
    return {
        "id": case["id"],
        "procedure": case["procedure"],
        "language": case["language"],
        "days_since": case["days_since"],
        "boundary": case.get("boundary", False),
        "gold": case["gold_verdict"],
        "rule_matched": matched,
        "raw_verdicts": raw,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0, help="0=전체")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    _ensure_key()
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY 없음 — vault/env 확인 필요"); sys.exit(1)

    cases = _load_cases()
    if args.limit:
        cases = _stratify(cases, args.limit)

    done_ids = set()
    if RESULTS.exists():
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done_ids.add(json.loads(line)["id"])
    todo = [c for c in cases if c["id"] not in done_ids]
    print(f"평가 대상 {len(cases)}건 중 미완 {len(todo)}건 (k={args.k}) 실행")

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("a", encoding="utf-8") as out:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            for res in ex.map(lambda c: _run_case(c, args.k), todo):
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
                out.flush()
                print(f"  [{res['id']}] gold={res['gold']} rule={bool(res['rule_matched'])} raw={res['raw_verdicts']}")
    print(f"완료 → {RESULTS}")


if __name__ == "__main__":
    main()
