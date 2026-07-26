"""공유 계약 — Pydantic 스키마. 모든 모듈(redflags·kb·judge·gate·triage)이 이걸 참조.

3-way verdict는 enum으로 고정 — LLM이 변형하면 파이프라인이 깨지므로(구조화 출력+retry로 강제).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Procedure(str, Enum):
    쌍꺼풀 = "쌍꺼풀"
    코성형 = "코성형"
    필러 = "필러"


class Language(str, Enum):
    ko = "ko"
    ja = "ja"


class Verdict(str, Enum):
    정상 = "정상"          # 고확신 정상 경과 → 안심
    불확실 = "불확실"      # 기권(defer) → 의사에게
    레드플래그 = "레드플래그"  # 이상징후 → 즉시 에스컬레이션


class PatientInput(BaseModel):
    """환자 입력 — 증상 텍스트 + (선택)사진 + 시술·경과일."""
    symptom_text: str = Field(..., description="환자가 서술한 증상(원어)")
    procedure: Procedure
    days_since: int = Field(..., ge=0, description="시술 후 경과일")
    language: Language = Language.ko
    photo_path: str | None = Field(None, description="회복 사진 경로(선택)")


class Judgment(BaseModel):
    """LLM 판정 원출력 — 구조화 강제 대상(Pydantic 검증+retry)."""
    verdict: Verdict
    reasons: list[str] = Field(default_factory=list, description="판정 근거(원어)")
    kb_refs: list[str] = Field(default_factory=list, description="근거 KB 항목 ID(인용 강제)")


class TriageResult(BaseModel):
    """파이프라인 최종 결과 — 판정 + 게이트 confidence + 룰 매칭 + 출력 메시지."""
    verdict: Verdict
    confidence: float = Field(..., ge=0.0, le=1.0, description="기권 게이트 confidence(0~1)")
    abstained: bool = Field(False, description="게이트가 불확실로 기권했는가")
    reasons: list[str] = Field(default_factory=list)
    kb_refs: list[str] = Field(default_factory=list)
    red_flag_matched: list[str] = Field(default_factory=list, description="결정론 룰 매칭 결과")
    reassurance: str | None = Field(None, description="정상 시 다국어 안심·안내 메시지")
    escalation_summary: str | None = Field(None, description="레드플래그/기권 시 의사용 구조화·번역 요약")

    @property
    def image_note(self) -> str:
        return ""  # (AC-6에서 이미지 신뢰도 주석 채움)
