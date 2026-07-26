"""다국어 에스컬레이션·안심 메시지(AC-7.2).

- 레드플래그/불확실 → 한국 클리닉용 '구조화·번역 요약'(일본어 환자 입력을 한국어로 정리).
- 정상 → 환자 언어로 따뜻한 안심 + KB 근거 자가관리 안내.
- LLM 호출은 call_fn 주입 가능. 키/함수 없으면 결정론 템플릿 폴백(오프라인·verify Phase 1 통과).
- 어떤 경우에도 진단·처방 문구를 만들지 않는다(안내·정리만).
"""
from __future__ import annotations

from typing import Callable

from .config import has_api_key
from .schema import Language, PatientInput, TriageResult, Verdict

_SEVERITY_HINT = {
    Verdict.레드플래그: "이상징후 감지 — 신속한 의료진 확인이 필요합니다.",
    Verdict.불확실: "정상인지 판단이 어려워 의료진 확인을 권합니다.",
}


def _clinic_call_fn() -> Callable[[str, str], str] | None:
    if not has_api_key():
        return None
    from .config import SETTINGS, get_anthropic_client

    client = get_anthropic_client()

    def _call(system: str, user: str) -> str:
        msg = client.messages.create(
            model=SETTINGS.judge_model,
            max_tokens=500,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")

    return _call


def build_escalation(
    inp: PatientInput,
    result: TriageResult,
    *,
    call_fn: Callable[[str, str], str] | None = None,
) -> str:
    """클리닉(한국어)으로 넘길 구조화·번역 요약."""
    call = call_fn if call_fn is not None else _clinic_call_fn()
    hint = _SEVERITY_HINT.get(result.verdict, "")
    facts = (
        f"시술: {inp.procedure.value} / 경과일: {inp.days_since}일 / 입력언어: {inp.language.value}\n"
        f"환자 서술(원어): {inp.symptom_text}\n"
        f"판정: {result.verdict.value} (confidence {result.confidence:.2f})\n"
        f"매칭 룰: {', '.join(result.red_flag_matched) or '없음'}\n"
        f"근거: {'; '.join(result.reasons) or '없음'}"
    )
    if call is None:
        # 오프라인 템플릿 — 일본어 원문은 그대로 두되 한국어 구조화 헤더로 정리.
        return f"[클리닉 에스컬레이션 요약]\n{hint}\n{facts}"

    system = (
        "너는 한국 성형·피부 클리닉 코디네이터에게 전달할 '에스컬레이션 요약'을 쓴다. "
        "진단·처방은 절대 하지 말고, 환자 상태를 구조화해 정리만 한다. "
        "환자 서술이 일본어면 한국어로 번역해 함께 적는다. 간결한 한국어로."
    )
    return call(system, facts)


def build_reassurance(
    inp: PatientInput,
    kb_context: str,
    result: TriageResult,
    *,
    call_fn: Callable[[str, str], str] | None = None,
) -> str:
    """정상 판정 시 환자 언어로 안심 + KB 근거 자가관리 안내."""
    call = call_fn if call_fn is not None else _clinic_call_fn()
    if call is None:
        lang_word = "안심하셔도 좋은 경과 범위입니다." if inp.language == Language.ko else "順調な回復範囲です。"
        return f"{lang_word} (근거 KB: {', '.join(result.kb_refs) or '회복궤적'}) 이상 신호가 보이면 병원에 문의하세요."

    lang = "한국어" if inp.language == Language.ko else "일본어"
    system = (
        f"너는 시술 후 환자에게 {lang}로 따뜻하게 안심시키는 안내를 쓴다. "
        "진단·처방은 하지 말고, 제공된 KB 정상 회복궤적 근거로 '지금은 정상 범위'임을 알리고, "
        "언제 병원에 문의해야 하는지(이상 신호)만 덧붙인다. 3~4문장."
    )
    user = f"[KB 근거]\n{kb_context}\n\n[환자] {inp.procedure.value}, {inp.days_since}일차: {inp.symptom_text}"
    return call(system, user)
