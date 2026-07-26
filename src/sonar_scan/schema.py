"""공유 계약 — Sonar Scan Pydantic 스키마. collect·extract·reputation·sentiment·report가 참조.

익명 id(Clinic A/B/C)만 스키마에 흐른다. 실명은 anonymize의 로컬 매핑에만 존재.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Sentiment(str, Enum):
    긍정 = "긍정"
    중립 = "중립"
    부정 = "부정"


class ClinicSignal(BaseModel):
    """한 클리닉의 수집된 공개 신호(집계값 + 익명)."""
    clinic_id: str = Field(..., description="익명 id 예: Clinic A")
    source: str = Field(..., description="수집 공개 소스 URL/이름")
    review_count: int = 0
    avg_rating: float | None = None
    mention_count: int = 0
    review_texts: list[str] = Field(default_factory=list, description="감성·토픽용(리뷰어 PII 제거)")


class MarketingRef(BaseModel):
    """경쟁사 마케팅·프로모션에서 추출한 레퍼런스."""
    clinic_id: str
    hook: str = Field(..., description="후크/헤드라인")
    offer: str | None = Field(None, description="오퍼/프로모션")
    channel: str | None = Field(None, description="채널(블로그·인스타·플레이스 등)")
    category: str | None = Field(None, description="시술 카테고리")
    source: str = Field(..., description="출처 URL")


class SuccessHypothesis(BaseModel):
    """'왜 먹히는가' — 입증된 인과 아님, 항상 가설."""
    clinic_id: str
    hypothesis: str
    evidence_signals: list[str] = Field(default_factory=list, description="이 가설을 지지하는 관찰 신호")
    is_hypothesis: bool = Field(True, description="항상 True — 인과 확정 아님")


class ReputationScore(BaseModel):
    """투명 산출식 기반 평판 지수(수집셋 내 상대). 공식 순위 아님."""
    clinic_id: str
    composite: float = Field(..., description="0~1 정규화 composite")
    rank: int = Field(..., description="수집셋 내 상대순위(1=최상)")
    sentiment_dist: dict[str, int] = Field(default_factory=dict, description="긍/중/부 카운트")
    review_count: int = 0


class ScanResult(BaseModel):
    """대시보드 조립 결과."""
    refs: list[MarketingRef] = Field(default_factory=list)
    hypotheses: list[SuccessHypothesis] = Field(default_factory=list)
    reputation: list[ReputationScore] = Field(default_factory=list)
    our_clinic_id: str | None = Field(None, description="'우리 병원' 익명 대역 기준점")
    formula: str = Field("", description="평판 지수 산출식(투명 공개)")
    collection_note: str = Field("", description="수집 소스·건수·봇벽 등 정직 로그")
