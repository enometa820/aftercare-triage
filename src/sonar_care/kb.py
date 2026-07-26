"""회복궤적 KB 라우팅 — full-context 그라운딩(AC-3.1·3.2).

시술별 정상 회복궤적 YAML(`data/kb/recovery/{시술}.yaml`)을 로드해,
경과일에 맞는 구간 + 인접(직전·직후) 구간을 판정 LLM에 주입할
full-context 문자열로 조립하고, 사용된 항목 id 리스트를 반환한다.

원칙(기획.md 정직성 가드): KB에 없으면 지어내지 않는다. 여기 담긴 것은
"일반 회복 정보"이며 임상 지침·진단·처방이 아니다. 궤적을 벗어난 신호는
판정 LLM이 불확실/레드플래그로 기울이는 근거로만 쓴다.

인접 구간을 함께 주입하는 이유: "지금 며칠째면 여기까지는 정상"뿐 아니라
"직전엔 이랬고 곧 이렇게 가라앉아야 한다"는 궤적 맥락을 줘야, 경과 대비
너무 이르거나 늦은 증상을 판정 LLM이 벗어남으로 감지할 수 있다.
"""
from __future__ import annotations

from pathlib import Path

import yaml

try:
    from .schema import Procedure
except ImportError:  # `python src/sonar_care/kb.py`로 직접 실행하는 경우
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from sonar_care.schema import Procedure

# src/sonar_care/kb.py → parents[2] = 저장소 루트
KB_DIR = Path(__file__).resolve().parents[2] / "data" / "kb" / "recovery"


def _load(procedure: Procedure) -> dict:
    path = KB_DIR / f"{procedure.value}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"회복궤적 KB 없음: {path}")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _match_index(blocks: list[dict], days_since: int) -> int:
    """경과일이 속한 구간 인덱스. 마지막 구간 상한을 넘으면 마지막 구간에 매핑."""
    for i, b in enumerate(blocks):
        lo, hi = b["day_range"]
        if lo <= days_since <= hi:
            return i
    return len(blocks) - 1


def _render_block(b: dict) -> str:
    lines = [f"[{b['id']}] {b['label']}", "  정상 신호:"]
    for s in b.get("normal_signs", []):
        lines.append(f"    - {s}")
    lines.append("  경계 신호(정상 범위 밖 — 의료진 확인 권장):")
    for s in b.get("watch_signs", []):
        lines.append(f"    - {s}")
    lines.append(f"  출처: {b.get('source', '(출처 보강 필요)')}")
    return "\n".join(lines)


def route_kb(procedure: Procedure, days_since: int) -> tuple[str, list[str]]:
    """해당 시술 YAML을 로드 → 경과일 구간(+인접 구간)을 full-context 문자열로 조립.

    반환: (판정 LLM 주입용 문자열, 사용된 항목 id 리스트).
    """
    kb = _load(procedure)
    blocks = kb["blocks"]
    idx = _match_index(blocks, days_since)

    # 매칭 구간 + 인접(직전·직후) 구간 — 궤적 맥락 제공
    start = max(0, idx - 1)
    end = min(len(blocks), idx + 2)
    selected = blocks[start:end]
    ids = [b["id"] for b in selected]

    header = (
        f"# 정상 회복궤적 참고 — {kb['procedure']} (경과 {days_since}일)\n"
        f"# {kb['disclaimer']}\n"
        f"# 현재 경과일에 해당하는 구간: [{blocks[idx]['id']}]"
    )
    body = "\n\n".join(_render_block(b) for b in selected)
    return f"{header}\n\n{body}", ids


if __name__ == "__main__":
    import sys

    # Windows 콘솔(cp949)에서도 한글·em-dash가 깨지지 않게 utf-8로 출력
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # 스모크: 코성형, 5일 → 3-7일 구간이 반환되어야 함
    ctx, ids = route_kb(Procedure.코성형, 5)
    print(ctx)
    print("\n반환 id:", ids)
    assert "코성형-3-7일" in ids, "5일은 3-7일 구간에 매핑되어야 함"
    print("\n스모크 OK")
