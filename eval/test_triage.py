"""eval CI 게이트(AC-8.2) — pytest.

두 층:
1) 오프라인 파이프라인 불변식(주입 판정, 무키·무API) — 항상 CI에서 돈다.
2) 레드플래그 recall 게이트 — results.jsonl(실측 캐시)을 결정론 exact-match로 채점.
   놓친 레드플래그(gold=레드플래그인데 정상 예측)가 임계 초과면 빌드 실패(exit non-zero).

BP 정합: 3-way 이산 라벨은 judge-as-metric의 불안정을 피해 exact-match 결정론 채점(1순위).
results.jsonl이 없으면(실측 미실행) 레드플래그 테스트는 skip — 오프라인 불변식은 계속 검증.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "eval"))

from sonar_care.schema import Judgment, Language, PatientInput, Procedure, Verdict
from sonar_care.triage import triage

RESULTS = ROOT / "data" / "eval" / "results.jsonl"
MAX_MISSED_REDFLAG = 0  # CI 게이트: 놓친 레드플래그 허용 0


# ---- 1) 오프라인 불변식 (무키) ----

def test_redflag_rule_short_circuits():
    r = triage(PatientInput(symptom_text="통증이 심하고 피부가 창백해졌어요",
                            procedure=Procedure.필러, days_since=1, language=Language.ko))
    assert r.verdict == Verdict.레드플래그
    assert r.red_flag_matched  # 룰이 LLM 앞단에서 잡음


def test_normal_high_confidence():
    r = triage(PatientInput(symptom_text="붓기가 조금 있어요", procedure=Procedure.코성형,
                            days_since=5, language=Language.ko),
               k=7, sample_fn=lambda: Judgment(verdict=Verdict.정상, reasons=["정상"], kb_refs=["코성형-3-7일"]))
    assert r.verdict == Verdict.정상 and r.reassurance


def test_low_confidence_abstains():
    seq = iter([Verdict.정상, Verdict.불확실, Verdict.정상, Verdict.불확실, Verdict.불확실, Verdict.정상, Verdict.불확실])
    r = triage(PatientInput(symptom_text="잘 모르겠어요", procedure=Procedure.쌍꺼풀,
                            days_since=10, language=Language.ko),
               k=7, sample_fn=lambda: Judgment(verdict=next(seq), reasons=["경계"], kb_refs=[]))
    assert r.abstained and r.verdict == Verdict.불확실


def test_asymmetric_redflag_low_bar():
    seq = iter([Verdict.정상, Verdict.레드플래그, Verdict.정상, Verdict.레드플래그, Verdict.정상, Verdict.정상, Verdict.정상])
    r = triage(PatientInput(symptom_text="색이 이상해요", procedure=Procedure.코성형,
                            days_since=3, language=Language.ko),
               k=7, sample_fn=lambda: Judgment(verdict=next(seq), reasons=["의심"], kb_refs=[]))
    assert r.verdict == Verdict.레드플래그  # 2표로도 채택(보수적 안전)


# ---- 2) 레드플래그 recall 게이트 (실측 캐시 소비, 결정론) ----

def _load_results():
    if not RESULTS.exists():
        return None
    return [json.loads(l) for l in RESULTS.read_text(encoding="utf-8").splitlines() if l.strip()]


def test_redflag_recall_gate():
    rows = _load_results()
    if rows is None:
        pytest.skip("results.jsonl 없음 — eval/run_eval.py 실행 필요")
    from metrics import predict_B  # eval/ on path

    total_red = sum(1 for r in rows if r["gold"] == "레드플래그")
    if total_red == 0:
        pytest.skip("실측 셋에 레드플래그 gold 없음")
    missed = sum(1 for r in rows if r["gold"] == "레드플래그" and predict_B(r, 0.6, 2)[0] == "정상")
    assert missed <= MAX_MISSED_REDFLAG, f"놓친 레드플래그 {missed} > 허용 {MAX_MISSED_REDFLAG}"


def test_results_schema_valid():
    rows = _load_results()
    if rows is None:
        pytest.skip("results.jsonl 없음")
    valid = {"정상", "불확실", "레드플래그"}
    for r in rows:
        assert r["gold"] in valid
        assert all(v in valid for v in r["raw_verdicts"])


# ---- 3) 회차2 수정 불변식 (F1·F2·F6, 무키) ----

def test_f1_citation_enforced():
    # 정상 다수결이지만 KB 근거 인용이 비면 → 불확실로 강등(근거 없는 안심 금지).
    r = triage(PatientInput(symptom_text="괜찮은 것 같아요", procedure=Procedure.코성형,
                            days_since=5, language=Language.ko),
               k=5, sample_fn=lambda: Judgment(verdict=Verdict.정상, reasons=["정상"], kb_refs=[]))
    assert r.verdict == Verdict.불확실 and r.abstained


def test_f2_output_guard_blocks_prescription():
    from sonar_care.output_guard import enforce
    safe, hits = enforce("항생제를 복용하세요. 하루 500mg.", "ko")
    assert hits and "복용하세요" not in safe and "500mg" not in safe
    # 파이프라인: 정상인데 안심 문구에 처방이 섞이면 안전 문구로 대체 + 플래그.
    r = triage(PatientInput(symptom_text="붓기 조금", procedure=Procedure.코성형, days_since=5, language=Language.ko),
               k=5,
               sample_fn=lambda: Judgment(verdict=Verdict.정상, reasons=["정상"], kb_refs=["코성형-3-7일"]),
               reassurance_fn=lambda s, u: "항생제를 복용하세요")
    assert r.output_flagged and "항생제" not in (r.reassurance or "")


def test_f6_image_fusion_defers_on_disagreement():
    # 텍스트-only 판정(레드플래그)이 게이트(정상)와 다르면 → 이미지 불확실성↑ → 정상 강등·기권.
    r = triage(PatientInput(symptom_text="약간 부었어요", procedure=Procedure.코성형, days_since=5,
                            language=Language.ko, photo_path="dummy.png"),
               k=5,
               sample_fn=lambda: Judgment(verdict=Verdict.정상, reasons=["정상"], kb_refs=["코성형-3-7일"]),
               text_only_verdict=Verdict.레드플래그)
    assert r.verdict == Verdict.불확실 and r.abstained and r.image_note and "달라" in r.image_note
