"""참고구현 크롤러 — Scrapling으로 우리 기능 구현에 참고할 코드·설계를 긁어 refs/raw/에 저장.
정직: 공개 페이지만. 실패는 manifest에 그대로 남긴다. 재실행 가능."""
import os, time, json
from scrapling.fetchers import Fetcher

OUT = os.path.join(os.path.dirname(__file__), "raw")
os.makedirs(OUT, exist_ok=True)

# (name, url, mode)  mode: raw=본문 그대로(md/rst/코드) / text=본문텍스트+코드블록
TARGETS = [
    # --- 재사용 코드 (OSS README/소스: raw) ---
    ("uqlm-readme",        "https://raw.githubusercontent.com/cvs-health/uqlm/main/README.md", "raw"),
    ("deepeval-readme",    "https://raw.githubusercontent.com/confident-ai/deepeval/main/README.md", "raw"),
    ("promptfoo-readme",   "https://raw.githubusercontent.com/promptfoo/promptfoo/main/README.md", "raw"),
    ("nemo-guardrails-readme", "https://raw.githubusercontent.com/NVIDIA/NeMo-Guardrails/develop/README.md", "raw"),
    ("mapie-readme",       "https://raw.githubusercontent.com/scikit-learn-contrib/MAPIE/master/README.rst", "raw"),
    ("vlm-uncertainty-readme", "https://raw.githubusercontent.com/sinatayebati/vlm-uncertainty/main/README.md", "raw"),
    # --- 설계·방법 (docs/서비스: text+코드블록) ---
    ("deepeval-custom-metric", "https://deepeval.com/docs/metrics-custom", "text"),
    ("promptfoo-redteam",  "https://www.promptfoo.dev/docs/red-team/quickstart/", "text"),
    ("anthropic-agents",   "https://www.anthropic.com/engineering/building-effective-agents", "text"),
    ("anthropic-structured", "https://platform.claude.com/docs/en/build-with-claude/structured-outputs", "text"),
    # --- 학술 (arXiv: text) ---
    ("arxiv-medabstain",   "https://arxiv.org/abs/2601.12471", "text"),
    ("arxiv-conformal-abstention", "https://arxiv.org/abs/2405.01563", "text"),
    # --- 레퍼런스 서비스 (안전·트리아지 UX 문구: text) ---
    ("ada-health",         "https://ada.com/", "text"),
    ("postop-ai",          "https://www.postop.ai/", "text"),
]

def extract_code_blocks(page):
    blocks = []
    for sel in ("pre", "code"):
        try:
            for el in page.css(sel):
                t = el.get_all_text()
                if t and len(t.strip()) > 20:
                    blocks.append(t.strip())
        except Exception:
            pass
    # dedup 유지 순서
    seen, out = set(), []
    for b in blocks:
        if b not in seen:
            seen.add(b); out.append(b)
    return out

manifest = []
for name, url, mode in TARGETS:
    try:
        p = Fetcher.get(url, stealthy_headers=True)
        status = getattr(p, "status", "?")
        if mode == "raw":
            body = p.body or ""
            if isinstance(body, bytes):
                body = body.decode("utf-8", "replace")
            content = body
        else:
            text = p.get_all_text() or ""
            code = extract_code_blocks(p)
            code_str = "\n\n===CODE===\n\n".join(code[:30])
            content = f"## 본문 텍스트\n\n{text}\n\n## 코드 블록 ({len(code)}개)\n\n{code_str}"
        content = content[:45000]
        fn = os.path.join(OUT, f"{name}.md")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(f"<!-- source: {url} | status: {status} | via Scrapling -->\n\n{content}")
        manifest.append({"name": name, "url": url, "status": status, "saved_len": len(content)})
        print(f"[OK ] {name:26s} status={status} len={len(content)}")
    except Exception as e:
        manifest.append({"name": name, "url": url, "error": f"{type(e).__name__}: {e}"})
        print(f"[ERR] {name:26s} {type(e).__name__}: {e}")
    time.sleep(1.5)

with open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f"\ndone: {sum(1 for m in manifest if 'error' not in m)}/{len(manifest)} ok")
