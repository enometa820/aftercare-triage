"""파이프라인 오케스트레이션(AC-7.1).

입력 → 결정론 레드플래그 룰(rules-first) → KB 라우팅 → 판정+기권 게이트 → 3-way 출력.
- 레드플래그 룰 매칭 시 LLM 판정과 무관하게 즉시 레드플래그(short-circuit) — 룰이 LLM보다 앞선다.
- 그 외에는 KB full-context를 근거로 self-consistency 게이트가 정상/불확실/레드플래그를 결정.
- sample_fn·escalation_fn·reassurance_fn 주입 가능 — 테스트·오프라인은 가짜를 넣어 무키로 전 파이프라인 검증.
"""
from __future__ import annotations

from collections.abc import Callable

from .config import SETTINGS
from .escalation import build_escalation, build_reassurance
from .gate import gate
from .judge import judge_once
from .kb import route_kb
from .output_guard import enforce
from .redflags import match_redflags
from .schema import Judgment, PatientInput, TriageResult, Verdict


def triage(
    inp: PatientInput,
    *,
    k: int | None = None,
    threshold: float | None = None,
    sample_fn: Callable[[], Judgment] | None = None,
    escalation_fn: Callable[[str, str], str] | None = None,
    reassurance_fn: Callable[[str, str], str] | None = None,
    text_only_verdict: Verdict | None = None,
) -> TriageResult:
    # 1) rules-first — 결정론 응급/이상 신호. 매칭 시 즉시 레드플래그.
    matched = match_redflags(inp.symptom_text, inp.language, inp.procedure)
    if matched:
        result = TriageResult(
            verdict=Verdict.레드플래그,
            confidence=1.0,  # 룰은 결정론(확실)
            abstained=False,
            reasons=["결정론 레드플래그 룰 매칭 — LLM 판정 이전에 사람에게 넘김"],
            kb_refs=[],
            red_flag_matched=matched,
        )
        summary = build_escalation(inp, result, call_fn=escalation_fn)
        result.escalation_summary, result.output_flagged = enforce(summary, inp.language.value)
        return result

    # 2) KB 라우팅 — 경과일 대비 정상 회복궤적 근거.
    kb_context, kb_ids = route_kb(inp.procedure, inp.days_since)

    # 3) 판정 + 불확실성 기권 게이트.
    judgment, confidence, abstained = gate(
        inp, kb_context, kb_ids, k=k, threshold=threshold, sample_fn=sample_fn
    )

    result = TriageResult(
        verdict=judgment.verdict,
        confidence=confidence,
        abstained=abstained,
        reasons=judgment.reasons,
        kb_refs=judgment.kb_refs,
        red_flag_matched=[],
    )

    # 3.5) F6 이미지 비대칭 융합 — 사진이 있으면 텍스트-only 판정과 비교, 상이하면 불확실성↑.
    if inp.photo_path or text_only_verdict is not None:
        to_v = text_only_verdict
        if to_v is None:
            to_v = judge_once(inp, kb_context, kb_ids, include_image=False).verdict
        if to_v != result.verdict:
            result.image_note = f"이미지가 텍스트-only 판정({to_v.value})과 달라 불확실성↑ — defer 가중"
            if result.verdict == Verdict.정상:  # 비대칭: 이미지가 정상 확신을 흔들면 사람에게
                result.verdict = Verdict.불확실
                result.abstained = True
        else:
            result.image_note = "이미지·텍스트 판정 일치"

    # 4) 3-way 출력 (+ F2 출력 가드).
    if result.verdict == Verdict.정상:
        msg = build_reassurance(inp, kb_context, result, call_fn=reassurance_fn)
        result.reassurance, result.output_flagged = enforce(msg, inp.language.value)
    else:  # 불확실 / 레드플래그 → 의사에게
        msg = build_escalation(inp, result, call_fn=escalation_fn)
        result.escalation_summary, result.output_flagged = enforce(msg, inp.language.value)

    return result


__all__ = ["SETTINGS", "triage"]
