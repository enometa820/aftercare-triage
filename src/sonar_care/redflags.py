"""레드플래그 룰 — LLM 판정 앞단의 결정론 안전망.

파이프라인이 LLM에 넘기기 *전에* 결정론 키워드 룰로 응급·이상 신호를 먼저 잡는다.
권위 사칭·응급 오도 같은 프롬프트 공격이 LLM을 속여도, 이 룰은 순수 문자열 매칭이라
안 속는다("측정된 안전" — 못 믿을 상황을 룰이 먼저 사람에게 넘긴다).

- 룰은 「신호 감지」만 한다. 진단·처방·치료 지시가 아니다.
- 사전 정본 = ``data/redflags/{ko,ja}.yaml`` (언어별, 같은 룰 id).
- 매칭 = 정규화(공백 축약·소문자) 후 부분문자열 포함. 본문 전체 무차별 배제정규식은
  쓰지 않는다(오탐 폭발) — 사전에 등록된 구절만 본다.
- 레드플래그는 보수적으로(사람에게 넘기는 쪽) 잡는 게 설계 의도다.
"""
from __future__ import annotations

import re
from functools import cache
from pathlib import Path

import yaml

from .schema import Language, Procedure

# 사전 위치 = repo 루트의 data/redflags/. redflags.py = src/sonar_care/redflags.py 이므로
# parents[0]=sonar_care, parents[1]=src, parents[2]=repo 루트.
_REDFLAG_DIR = Path(__file__).resolve().parents[2] / "data" / "redflags"

_COMMON = "공통"  # 시술 무관 공통 룰의 procedure 태그


def _normalize(text: str) -> str:
    """매칭용 정규화 — 공백 축약 + 소문자. 한국어·일본어는 대소문자가 없지만
    영문 약어·숫자 표기를 안정적으로 잡기 위해 소문자화한다."""
    return re.sub(r"\s+", " ", text).strip().lower()


@cache
def _load_rules(language: Language) -> tuple[dict, ...]:
    """해당 언어 사전을 로드해 룰 리스트(tuple, 캐시용)로 반환."""
    path = _REDFLAG_DIR / f"{language.value}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"레드플래그 사전 없음: {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    rules = data.get("rules", [])
    # keywords도 미리 정규화해 매칭 비용을 낮춘다.
    normalized: list[dict] = []
    for rule in rules:
        normalized.append(
            {
                "id": rule["id"],
                "procedure": rule.get("procedure", _COMMON),
                "severity": rule.get("severity", "긴급"),
                "keywords": [_normalize(k) for k in rule.get("keywords", [])],
                "source": rule.get("source", ""),
            }
        )
    return tuple(normalized)


def match_redflags(text: str, language: Language, procedure: Procedure) -> list[str]:
    """증상 텍스트에서 응급·이상 신호 룰을 매칭해 매칭된 룰 id 리스트를 반환.

    공통 룰 + 해당 시술 룰만 대상으로 한다(타 시술 룰은 무시).
    한 룰의 키워드 중 하나라도 정규화 텍스트에 부분문자열로 포함되면 매칭.
    """
    norm = _normalize(text)
    if not norm:
        return []

    matched: list[str] = []
    for rule in _load_rules(language):
        if rule["procedure"] not in (_COMMON, procedure.value):
            continue
        if any(kw and kw in norm for kw in rule["keywords"]):
            matched.append(rule["id"])
    return matched


if __name__ == "__main__":
    import sys

    # Windows 기본 콘솔(cp949)에서 일본어 출력이 깨지지 않게 UTF-8로 재설정.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # 스모크 — 필러 + "통증이 심하고 피부가 창백" → 혈관폐색 룰이 잡혀야 한다.
    sample = "시술한 지 하루 됐는데 통증이 심하고 피부가 창백해졌어요"
    hits = match_redflags(sample, Language.ko, Procedure.필러)
    print(f"입력: {sample}")
    print(f"매칭된 룰: {hits}")
    assert "filler_vascular_occlusion" in hits, "혈관폐색 룰이 매칭돼야 한다"

    # 일본어 사전도 같은 신호를 잡는지 확인.
    ja_sample = "施術した部位の皮膚が蒼白になって、どんどん強くなる痛みがあります"
    ja_hits = match_redflags(ja_sample, Language.ja, Procedure.필러)
    print(f"入力: {ja_sample}")
    print(f"一致したルール: {ja_hits}")
    assert "filler_vascular_occlusion" in ja_hits, "血管閉塞ルールが一致すべき"

    # 시술 격리 — 필러 텍스트에 쌍꺼풀 전용 룰이 섞여선 안 된다(공통만 공유).
    eye_only = match_redflags("눈이 튀어나온 것 같아요", Language.ko, Procedure.필러)
    assert "eye_proptosis" not in eye_only, "타 시술 룰은 매칭되면 안 된다"

    print("스모크 통과 ✓")
