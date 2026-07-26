"""대시보드(AC-7) — scan_result.json을 자체완결 정적 HTML로. 익명·공개 안전.

"경쟁 레퍼런스 + 성공요인 가설 + 우리 상대순위·감성" 한 화면. CDN 0.
산출: docs/scan-dashboard.html
"""
from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data" / "scan" / "scan_result.json"
OUT = ROOT / "docs" / "scan-dashboard.html"


def _esc(s) -> str:
    return html.escape(str(s or ""))


def build() -> Path:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    rep = d["reputation"]
    # 언급 희소 정직 노트
    discriminating = sum(1 for r in rep if r["review_count"] >= 2)
    sparse_note = (
        f"※ 정직: 공개 블로그 언급이 클리닉당 대부분 1건이라(언급 2건+ = {discriminating}/{len(rep)}곳) "
        "지수 변별력이 약하다(다수 동점). 리뷰수·플레이스 평점 등 신호 보강 시 변별력↑. "
        "레퍼런스·성공요인이 이 모듈의 핵심 산출물."
    )
    rep_rows = "".join(
        f"<tr><td>{r['rank']}</td><td>{_esc(r['clinic_id'])}</td><td>{r['composite']}</td>"
        f"<td>{r['review_count']}</td><td>긍{r['sentiment_dist'].get('긍정',0)}·중{r['sentiment_dist'].get('중립',0)}·부{r['sentiment_dist'].get('부정',0)}</td></tr>"
        for r in rep
    )
    ref_rows = "".join(
        f"<li><b>[{_esc(r['category'])}]</b> {_esc(r['hook'])}"
        + (f" <span class='offer'>· {_esc(r['offer'])}</span>" if r.get("offer") else "")
        + f" <span class='cid'>{_esc(r['clinic_id'])}</span></li>"
        for r in d["refs"]
    )
    hyp_rows = "".join(
        f"<li>{_esc(h['hypothesis'])} <span class='tag'>(가설)</span>"
        + (f"<div class='ev'>근거: {_esc(' · '.join(h['evidence_signals']))}</div>" if h.get("evidence_signals") else "")
        + "</li>"
        for h in d["hypotheses"]
    )
    page = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sonar Scan — 경쟁·평판 마케팅 인텔</title>
<style>
body{{margin:0;font-family:system-ui,'Segoe UI',sans-serif;background:#0f1720;color:#e6edf3;}}
header{{padding:20px 28px;border-bottom:1px solid #2a3b4d;}}
h1{{margin:0;font-size:20px;}} .sub{{color:#9fb0c0;font-size:13px;margin-top:4px;}}
.wrap{{display:grid;grid-template-columns:1fr 1fr;gap:20px;padding:24px 28px;max-width:1200px;}}
@media(max-width:860px){{.wrap{{grid-template-columns:1fr;}}}}
.card{{background:#172230;border:1px solid #2a3b4d;border-radius:12px;padding:18px;}}
h3{{margin:0 0 8px;}} table{{width:100%;border-collapse:collapse;font-size:13px;}}
td,th{{border-bottom:1px solid #2a3b4d;padding:6px 8px;text-align:left;}}
ul{{margin:0;padding-left:18px;}} li{{margin:8px 0;font-size:14px;line-height:1.5;}}
.offer{{color:#2ea043;}} .cid{{color:#9fb0c0;font-size:12px;}}
.tag{{color:#d29922;font-size:12px;}} .ev{{color:#9fb0c0;font-size:12px;margin-top:2px;}}
.note{{color:#9fb0c0;font-size:12px;line-height:1.5;margin-top:10px;}}
.formula{{background:#0d1520;border:1px solid #2a3b4d;border-radius:8px;padding:8px;font-size:12px;color:#9fb0c0;}}
</style></head><body>
<header><h1>🛰️ Sonar Scan <span class="sub">— 경쟁·평판 마케팅 인텔 (refradar 재현)</span></h1>
<div class="sub">공개 신호(네이버 view) 실크롤 · 병원명 익명(Clinic A/B/C) · 리뷰어 PII 0 · 성공요인=가설 · 순위=투명지수(공식 아님)</div></header>
<div class="wrap">
  <div class="card"><h3>경쟁 마케팅 레퍼런스 ({len(d['refs'])}건)</h3><ul>{ref_rows}</ul></div>
  <div class="card"><h3>성공요인 (가설)</h3><ul>{hyp_rows}</ul>
    <div class="note">각 항목은 LLM 추론 <b>가설</b>이며 입증된 인과가 아니다.</div></div>
  <div class="card" style="grid-column:1/-1;"><h3>평판 상대순위 (투명 지수 · 수집셋 내)</h3>
    <table><tr><th>순위</th><th>클리닉</th><th>composite</th><th>언급</th><th>감성</th></tr>{rep_rows}</table>
    <div class="formula">{_esc(d['formula'])}</div>
    <div class="note">{_esc(sparse_note)}</div>
    <div class="note">{_esc(d['collection_note'])}</div></div>
</div></body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"saved {p}")
