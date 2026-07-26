"""익명화(AC-3) — 실명 병원 → Clinic A/B/C. 공개 산출물엔 익명만.

실명↔익명 매핑은 `_local/scan_anon_map.json`(gitignore)에만. 결정론(같은 실명=같은 라벨).
공개 레포에 실명 병원 평판·순위를 박지 않기 위함(명예·PII 리스크).
"""
from __future__ import annotations

import json
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "_local" / "scan_anon_map.json"


class Anonymizer:
    def __init__(self) -> None:
        self._map: dict[str, str] = {}
        if MAP_PATH.exists():
            self._map = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    def anon(self, name: str | None) -> str | None:
        if not name:
            return None
        key = name.strip()
        if key not in self._map:
            self._map[key] = f"Clinic {self._label(len(self._map))}"
        return self._map[key]

    @staticmethod
    def _label(i: int) -> str:
        # A..Z, AA, AB...
        if i < 26:
            return string.ascii_uppercase[i]
        return string.ascii_uppercase[i // 26 - 1] + string.ascii_uppercase[i % 26]

    def scrub(self, text: str | None) -> str | None:
        """자유 텍스트에서 알려진 실명 병원을 익명 id로 치환(방어 심층화)."""
        if not text:
            return text
        out = text
        # 긴 이름부터 치환(부분 겹침 방지)
        for name in sorted(self._map, key=len, reverse=True):
            if name and name in out:
                out = out.replace(name, self._map[name])
        return out

    def known_names(self) -> list[str]:
        return list(self._map)

    def save(self) -> None:
        MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        MAP_PATH.write_text(json.dumps(self._map, ensure_ascii=False, indent=2), encoding="utf-8")
