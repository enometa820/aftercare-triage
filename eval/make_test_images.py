"""도식 합성 이미지 생성 — 멀티모달 defer 경로 기계 검증용.

★정직: 이것은 실제 의료영상이 아니다. matplotlib로 그린 추상 도식(얼굴 윤곽 + 색 패치)이며
'SYNTHETIC — NOT A MEDICAL IMAGE'를 이미지에 각인한다. 사실적 의료사진을 지어내지 않는다(공개 레포 오인 방지).
목적 = judge의 이미지 입력 경로가 실제로 도는지 + 비임상 이미지에서 VLM이 불확실→defer 하는지 확인.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse

OUT = Path(__file__).resolve().parents[1] / "data" / "eval" / "images"


def _face(path: Path, patch_color: str, label: str) -> None:
    fig, ax = plt.subplots(figsize=(3, 3.5))
    ax.add_patch(Ellipse((0.5, 0.55), 0.6, 0.8, facecolor="#f2d3b8", edgecolor="#c9a"))
    ax.add_patch(Ellipse((0.38, 0.62), 0.12, 0.06, facecolor="white", edgecolor="#333"))
    ax.add_patch(Ellipse((0.62, 0.62), 0.12, 0.06, facecolor="white", edgecolor="#333"))
    ax.add_patch(Ellipse((0.38, 0.55), 0.16, 0.08, facecolor=patch_color, alpha=0.5))  # 도식 색패치
    ax.text(0.5, 0.06, "SYNTHETIC — NOT A MEDICAL IMAGE", ha="center", fontsize=7, color="crimson")
    ax.text(0.5, 0.95, label, ha="center", fontsize=8)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=90); plt.close(fig)


def main() -> list[Path]:
    a = OUT / "schematic_mild.png"
    b = OUT / "schematic_dark.png"
    _face(a, "#f0c0a0", "schematic A (mild tint)")
    _face(b, "#7040a0", "schematic B (dark patch)")
    print("saved:", a.name, b.name)
    return [a, b]


if __name__ == "__main__":
    main()
