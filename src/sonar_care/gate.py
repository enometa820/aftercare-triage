"""불확실성 기권 게이트(AC-5.1) + 이미지 defer(AC-6).

핵심 명제의 심장 — "못 믿으면 사람에게 넘긴다".
- self-consistency: 같은 입력을 k회 재샘플(temperature>0)해 판정이 갈리는 정도로 confidence 산출.
  Claude는 token logprob이 없으므로 빈도 기반이 정석(BP §A). semantic entropy(uqlm)는 torch/NLI가
  필요해 데모엔 과함 — 동일 원리를 네이티브로 구현하고 uqlm은 대체재로 문서화.
- 비대칭 융합(AC-6 취지 포함): '정상'은 고확신을 요구하고, '레드플래그'는 낮은 표로도 이긴다
  (레드플래그 놓침 = 치명, 그래서 보수적으로 사람에게 넘긴다).
- 이미지가 있으면 판정 샘플에 포함되며, 이미지가 애매하면 표가 갈려 confidence가 자연히 떨어져
  기권으로 이어진다(defer-by-default) — 이미지 '정확도'는 주장하지 않는다.
- sample_fn 주입 가능 — 테스트·오프라인은 스크립트된 판정을 넣는다.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable

from .config import SETTINGS
from .schema import Judgment, PatientInput, Verdict


def _default_sample_fn(inp: PatientInput, kb_context: str, kb_ids: list[str]) -> Callable[[], Judgment]:
    """실제 Claude 1회 판정 샘플 함수(키 필요)."""
    from .judge import judge_once

    def _sample() -> Judgment:
        return judge_once(inp, kb_context, kb_ids, temperature=1.0)

    return _sample


def gate(
    inp: PatientInput,
    kb_context: str,
    kb_ids: list[str],
    *,
    k: int | None = None,
    threshold: float | None = None,
    red_min: int | None = None,
    sample_fn: Callable[[], Judgment] | None = None,
) -> tuple[Judgment, float, bool]:
    """k회 self-consistency로 최종 판정·confidence·기권여부를 낸다.

    반환: (최종 Judgment, confidence 0~1, abstained)
    red_min = 레드플래그 채택에 필요한 최소 표수(기본 2, 안전 쪽으로 낮게). 캘리브레이션으로 튜닝.
    """
    k = k or SETTINGS.num_samples
    threshold = threshold if threshold is not None else SETTINGS.abstain_threshold
    sample = sample_fn or _default_sample_fn(inp, kb_context, kb_ids)

    samples = [sample() for _ in range(k)]
    counts = Counter(j.verdict for j in samples)

    # 비대칭: 레드플래그는 낮은 표(기본 2표)로도 채택 — 놓침이 치명적이라 과에스컬 쪽으로.
    red_min = red_min if red_min is not None else min(2, k)
    if counts.get(Verdict.레드플래그, 0) >= red_min:
        rep = next(j for j in samples if j.verdict == Verdict.레드플래그)
        conf = counts[Verdict.레드플래그] / k
        return (
            Judgment(verdict=Verdict.레드플래그, reasons=rep.reasons, kb_refs=rep.kb_refs),
            conf,
            False,
        )

    # 그 외 = 다수결. 다수 confidence가 임계 미만이면 기권(불확실).
    top_verdict, top_count = counts.most_common(1)[0]
    conf = top_count / k
    rep = next(j for j in samples if j.verdict == top_verdict)

    if top_verdict == Verdict.정상 and conf < threshold:
        # 정상은 고확신을 요구 — 미달이면 사람에게 넘긴다.
        return (
            Judgment(
                verdict=Verdict.불확실,
                reasons=[f"정상 확신 부족(consistency {conf:.2f} < {threshold})"] + rep.reasons,
                kb_refs=rep.kb_refs,
            ),
            conf,
            True,
        )

    if top_verdict == Verdict.불확실:
        return (rep, conf, True)

    return (Judgment(verdict=top_verdict, reasons=rep.reasons, kb_refs=rep.kb_refs), conf, False)
