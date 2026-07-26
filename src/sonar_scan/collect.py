"""수집(AC-2) — Scrapling으로 공개 소스(네이버 통합검색 view) 클리닉 마케팅·리뷰 신호 수집.

- 실측 결과: 네이버 view 검색은 정적 Scrapling으로 실텍스트 확보(코성형 후기 등). 구글·네이버맵은 봇벽 → 미사용(우회 안 함, ToS 준수).
- 수집 = 공개 블로그 검색 결과 텍스트(제목·스니펫). 리뷰어 개인정보는 저장·파싱 안 함(집계·공개 스니펫만).
- raw 텍스트는 data/scan/raw/(gitignore, 제3자·실명). 추출(extract)이 여기서 익명 구조화.
- collection_note에 소스·건수·봇벽을 정직 기록.

사용: .venv/Scripts/python.exe -m sonar_scan.collect  (src on path)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "scan" / "raw"

# 데모 질의 — 성형·피부 시술 + 마케팅/후기 신호. (공개 검색어)
QUERIES = [
    "코성형 후기",
    "쌍꺼풀 이벤트",
    "필러 후기",
    "강남 성형외과 이벤트",
    "눈성형 부작용 후기",
]
NAVER_VIEW = "https://search.naver.com/search.naver?where=view&query={}"


def _slug(q: str) -> str:
    return re.sub(r"\s+", "_", q.strip())


def collect(queries: list[str] | None = None) -> dict:
    """네이버 view 검색을 실크롤해 raw 텍스트 저장 + manifest 반환."""
    from scrapling.fetchers import Fetcher

    queries = queries or QUERIES
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = []
    for q in queries:
        url = NAVER_VIEW.format(quote(q))
        try:
            p = Fetcher.get(url, stealthy_headers=True)
            text = p.get_all_text() or ""
            (RAW / f"{_slug(q)}.txt").write_text(text, encoding="utf-8")
            manifest.append({"query": q, "source": url, "textlen": len(text), "ok": len(text) > 500})
        except Exception as e:  # noqa: BLE001 — 크롤은 다양한 실패 가능, 로그하고 계속
            manifest.append({"query": q, "source": url, "error": f"{type(e).__name__}: {e}", "ok": False})
    note = (
        f"네이버 통합검색(view) {sum(m.get('ok') for m in manifest)}/{len(manifest)}건 실크롤. "
        "구글·네이버맵은 봇벽으로 정적 크롤 불가 → 미사용(ToS 준수, 우회 안 함). "
        "리뷰어 개인정보 미수집(공개 스니펫·집계만)."
    )
    (RAW / "_manifest.json").write_text(
        json.dumps({"manifest": manifest, "note": note}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"manifest": manifest, "note": note}


if __name__ == "__main__":
    r = collect()
    print(r["note"])
    for m in r["manifest"]:
        print(f"  [{m['query']}] {'ok' if m.get('ok') else 'x'} len={m.get('textlen', 0)}")
