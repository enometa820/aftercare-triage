"""평판 지수·상대순위(AC-5) — 투명 산출식. 공식 순위 재현 아님.

공개 신호(블로그 언급량 + 감성)를 정규화·가중 합산한 composite로 수집셋 내 상대순위를 낸다.
산출식을 그대로 공개(블랙박스 아님). 리뷰수·평점이 확보되면 가중에 추가 가능.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .schema import ReputationScore

FORMULA = (
    "composite = 0.6*norm(mention_count) + 0.4*sentiment_score ; "
    "sentiment_score=(긍정-부정)/max(1,총언급) 을 0~1로 시프트. "
    "공개 블로그 언급·감성 기반 투명지수 — 네이버·강남언니 공식 순위 재현 아님."
)


def compute(mentions: list[dict]) -> list[ReputationScore]:
    by: dict[str, list[str]] = defaultdict(list)
    for m in mentions:
        if m.get("clinic"):
            by[m["clinic"]].append(m.get("sentiment", "중립"))
    if not by:
        return []
    max_mention = max(len(v) for v in by.values()) or 1
    rows = []
    for cid, sents in by.items():
        c = Counter(sents)
        total = len(sents)
        sent_score = ((c.get("긍정", 0) - c.get("부정", 0)) / max(1, total) + 1) / 2  # 0~1
        composite = 0.6 * (len(sents) / max_mention) + 0.4 * sent_score
        rows.append(ReputationScore(
            clinic_id=cid, composite=round(composite, 3), rank=0,
            sentiment_dist={"긍정": c.get("긍정", 0), "중립": c.get("중립", 0), "부정": c.get("부정", 0)},
            review_count=total,
        ))
    rows.sort(key=lambda r: r.composite, reverse=True)
    for i, r in enumerate(rows, 1):
        r.rank = i
    return rows
