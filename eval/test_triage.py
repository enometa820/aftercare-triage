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
