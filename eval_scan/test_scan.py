"""M2 eval·정직 테스트(AC-8) — pytest. 무키(주입 LLM·캐시 소비).

핵심: 익명화 동작 / 공개 산출물 실명·PII 잔존 0 / 성공요인 가설 라벨 / 평판 산출식 결정론.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sonar_scan import reputation
from sonar_scan.anonymize import Anonymizer
from sonar_scan.extract import extract_blob
from sonar_scan.schema import SuccessHypothesis

SCAN = ROOT / "data" / "scan" / "scan_result.json"
MAP = ROOT / "_local" / "scan_anon_map.json"


def test_anonymize_maps_and_scrubs():
    a = Anonymizer.__new__(Anonymizer)
    a._map = {}
    id1 = a.anon("온누리안과병원")
    assert id1.startswith("Clinic ")
    assert a.anon("온누리안과병원") == id1  # 결정론
    scrubbed = a.scrub("예쁜 눈 성형, 온누리안과병원 이벤트")
    assert "온누리안과병원" not in scrubbed and id1 in scrubbed


def test_reputation_deterministic():
    mentions = [{"clinic": "Clinic A", "sentiment": "긍정"}, {"clinic": "Clinic A", "sentiment": "긍정"},
                {"clinic": "Clinic B", "sentiment": "부정"}]
    rows = reputation.compute(mentions)
    ranks = {r.clinic_id: r.rank for r in rows}
    assert ranks["Clinic A"] == 1 and ranks["Clinic B"] == 2  # 언급 많고 긍정인 A가 상위


def test_extract_offline_injected():
    fake = lambda s, u: '{"refs":[{"clinic":"X의원","hook":"자연스러운 코","offer":null,"channel":"블로그","category":"코성형"}],"mentions":[{"clinic":"X의원","sentiment":"긍정"}]}'
    d = extract_blob("아무 텍스트", call_fn=fake)
    assert d["refs"][0]["category"] == "코성형" and d["mentions"][0]["sentiment"] == "긍정"


def test_hypotheses_flagged_as_hypothesis():
    h = SuccessHypothesis(clinic_id="Clinic A", hypothesis="가격 명시가 클릭 유도", evidence_signals=["오퍼 문구"])
    assert h.is_hypothesis is True


# ---- 정직·안전 가드 (커밋 산출물 소비) ----

def test_no_realname_leak_in_public():
    if not (SCAN.exists() and MAP.exists()):
        pytest.skip("scan_result.json / 익명맵 없음 — run_scan 미실행")
    pub = SCAN.read_text(encoding="utf-8")
    mp = json.loads(MAP.read_text(encoding="utf-8"))
    leaks = [n for n in mp if n and n in pub]
    assert not leaks, f"공개 산출물에 실명 잔존: {leaks[:3]}"


def test_public_output_hypothesis_and_transparency():
    if not SCAN.exists():
        pytest.skip("scan_result.json 없음")
    d = json.loads(SCAN.read_text(encoding="utf-8"))
    assert all(h["is_hypothesis"] for h in d["hypotheses"])          # 성공요인=가설
    assert d["formula"] and "공식 순위" in d["formula"]              # 투명·공식아님 명시
    assert "PII 0" in d["collection_note"]                            # 정직 로그
    assert all(r["clinic_id"].startswith("Clinic") or r["clinic_id"] == "미상" for r in d["reputation"])
