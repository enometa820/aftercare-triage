"""설정 + LLM 클라이언트 팩토리.

- API 키는 환경변수(vault 주입)에서만 읽는다. 평문 저장·로그 0.
- 무거운 import(anthropic·langchain)는 팩토리 안에서 지연 로드 — 키·SDK 없이도 모듈 import·테스트가 되게.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # 판정 모델(구조화 출력·VLM 멀티모달)
    judge_model: str = os.getenv("SONAR_JUDGE_MODEL", "claude-sonnet-5")
    # 기권 게이트 self-consistency 샘플 수
    num_samples: int = int(os.getenv("SONAR_NUM_SAMPLES", "7"))
    # 게이트 임계값(캘리브레이션 산출값으로 덮임; 없으면 이 기본값)
    abstain_threshold: float = float(os.getenv("SONAR_ABSTAIN_THRESHOLD", "0.6"))
    # 목표 miscoverage(컨포멀 alpha)
    conformal_alpha: float = float(os.getenv("SONAR_CONFORMAL_ALPHA", "0.10"))

    @property
    def anthropic_api_key(self) -> str | None:
        return os.getenv("ANTHROPIC_API_KEY")


SETTINGS = Settings()


def has_api_key() -> bool:
    return bool(SETTINGS.anthropic_api_key)


def get_anthropic_client():
    """anthropic.Anthropic 클라이언트. 키·SDK 없으면 명확히 실패."""
    if not has_api_key():
        raise RuntimeError("ANTHROPIC_API_KEY 미설정 — vault에서 환경변수로 주입 필요")
    from anthropic import Anthropic  # 지연 import

    return Anthropic(api_key=SETTINGS.anthropic_api_key)


def get_langchain_chat(temperature: float = 1.0):
    """uqlm용 LangChain ChatAnthropic. self-consistency엔 temperature>0 필요."""
    if not has_api_key():
        raise RuntimeError("ANTHROPIC_API_KEY 미설정 — vault에서 환경변수로 주입 필요")
    from langchain_anthropic import ChatAnthropic  # 지연 import

    return ChatAnthropic(
        model=SETTINGS.judge_model,
        temperature=temperature,
        api_key=SETTINGS.anthropic_api_key,
    )
