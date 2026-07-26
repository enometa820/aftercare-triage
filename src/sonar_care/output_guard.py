"""출력 가드(F2) — 진단·처방·용량 표현의 결정론 필터.

시스템프롬프트가 진단·처방을 금해도(judge.py), 모델 출력이 우연히 처방·용량 문구를
낼 수 있다. 환자·클리닉에 나가기 전 마지막 결정론 방어선 — 감지 시 안전 문구로 대체.
- 방어 심층화(defense-in-depth): 프롬프트(1차) + 이 필터(2차).
- 한/일 표현 모두 커버. 감지 패턴은 보수적으로(오탐보다 미탐이 위험).
"""
from __future__ import annotations

import re

# 진단명 확정·처방·용량 지시 표현(한/일). 안내·정상범위 설명과 구분되게 좁게 잡는다.
_BANNED = [
    r"처방(해|하|드림|합니다|해드)",
    r"복용하세요",
    r"드세요",
    r"\d+\s*mg",
    r"항생제를?\s*(드|복용|처방)",
    r"진단명은",
    r"약을\s*(드|복용)",
    r"投与",
    r"処方",
    r"服用してください",
    r"mgを",
]
_PATTERNS = [re.compile(p) for p in _BANNED]

_SAFE_KO = "※ 구체적 진단·처방·약물 용량은 제공하지 않습니다. 정확한 판단은 담당 의료진에게 문의하세요."
_SAFE_JA = "※ 具体的な診断・処方・薬の用量は提供しません。担当医にご相談ください。"


def scan(text: str | None) -> list[str]:
    if not text:
        return []
    return [p.pattern for p in _PATTERNS if p.search(text)]


def enforce(text: str | None, language: str = "ko") -> tuple[str | None, list[str]]:
    """감지 시 (안전 대체문, 감지패턴 목록) 반환. 없으면 (원문, [])."""
    hits = scan(text)
    if not hits:
        return text, []
    safe = _SAFE_JA if language == "ja" else _SAFE_KO
    return safe, hits
