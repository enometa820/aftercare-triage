"""M2 파이프라인 러너 — 수집→추출→익명화→평판→가설→익명 ScanResult 커밋본.

실 LLM(추출·가설)은 여기서만. 산출 data/scan/scan_result.json = 익명·공개 안전(실명 0).
사용: .venv/Scripts/python.exe eval_scan/run_scan.py
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "data" / "scan" / "scan_result.json"


def _key() -> None:
    if os.getenv("ANTHROPIC_API_KEY"):
        return
    v = Path.home() / ".vault" / "enometa-distill" / ".env.local"
    if v.exists():
        m = re.search(r"^ANTHROPIC_API_KEY=(.+)$", v.read_text(encoding="utf-8"), re.MULTILINE)
        if m:
            os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip().strip('"').strip("'")


def main() -> None:
    _key()
    from sonar_scan import extract, reputation
    from sonar_scan.anonymize import Anonymizer
    from sonar_scan.collect import RAW, collect
    from sonar_scan.schema import MarketingRef, ReputationScore, ScanResult, SuccessHypothesis

    note = "네이버 view 공개 크롤(구글·맵 봇벽 미사용)."
    if not list(RAW.glob("*.txt")):
        r = collect()
        note = r["note"]

    raw = extract.extract_all()  # 실명 포함(인메모리)
    anon = Anonymizer()

    # 1) 모든 실명(refs+mentions) 등록 → scrub에 완전한 맵
    for r in raw["refs"]:
        anon.anon(r.get("clinic"))
    for m in raw["mentions"]:
        anon.anon(m.get("clinic"))

    # 2) refs 익명화 + hook/offer 실명 스크럽(방어 심층화)
    refs_anon = []
    for r in raw["refs"]:
        refs_anon.append(MarketingRef(
            clinic_id=anon.anon(r.get("clinic")) or "미상",
            hook=(anon.scrub(r.get("hook")) or "")[:200], offer=anon.scrub(r.get("offer")),
            channel=r.get("channel"), category=r.get("category"), source="네이버 view(공개)",
        ).model_dump())
    mentions_anon = [{"clinic": anon.anon(m.get("clinic")), "sentiment": m.get("sentiment", "중립")}
                     for m in raw["mentions"] if m.get("clinic")]
    anon.save()

    rep = reputation.compute(mentions_anon)
    hyps_raw = extract.hypotheses(refs_anon)
    hyps = [SuccessHypothesis(clinic_id=h.get("clinic") or "미상", hypothesis=h.get("hypothesis", ""),
                              evidence_signals=h.get("evidence_signals", []) or []).model_dump()
            for h in hyps_raw]

    our = rep[len(rep) // 2].clinic_id if rep else None  # 데모 기준점(중앙값 익명 대역)
    result = ScanResult(
        refs=[MarketingRef(**r) for r in refs_anon],
        hypotheses=[SuccessHypothesis(**h) for h in hyps],
        reputation=[ReputationScore(**r.model_dump()) for r in rep],
        our_clinic_id=our, formula=reputation.FORMULA,
        collection_note=note + f" 익명 클리닉 {len(rep)}곳·레퍼런스 {len(refs_anon)}건·가설 {len(hyps)}건. 성공요인=가설, 순위=투명지수(공식 아님), 리뷰어 PII 0.",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(f"saved {OUT.name}: 클리닉 {len(rep)}·레퍼런스 {len(refs_anon)}·가설 {len(hyps)}")
    print("top rep:", [(r.clinic_id, r.composite, r.rank) for r in rep[:5]])


if __name__ == "__main__":
    main()
