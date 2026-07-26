"""추출(AC-4·AC-6) — LLM으로 수집 텍스트에서 마케팅 레퍼런스 + 클리닉 언급(감성) 구조화.

- 입력 = collect가 저장한 공개 블로그 검색 텍스트(실명 포함, gitignore raw).
- 출력(원본, 실명) = 인메모리 → anonymize가 익명화한 것만 커밋. 실명은 로컬 밖으로 안 나감.
- 성공요인은 별도(extract는 레퍼런스·언급·감성만). call_fn 주입 = 무키 테스트.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "scan" / "raw"

SYS = """너는 성형·피부 마케팅 인텔 분석가다. 네이버 통합검색(블로그/후기) 텍스트에서 아래를 JSON으로만 추출하라(다른 말 금지).
{"refs":[{"clinic":"병원/의원 이름 또는 null","hook":"후크/제목 한 줄","offer":"프로모션/오퍼 또는 null","channel":"블로그|플레이스|기타","category":"코성형|쌍꺼풀|필러|눈성형|기타"}],
 "mentions":[{"clinic":"병원 이름","sentiment":"긍정|중립|부정"}]}
규칙: 실제 텍스트에 등장한 병원명·후크만. 없으면 clinic=null. 개인(리뷰어) 이름·연락처는 절대 포함하지 마라. 광고성 제목은 hook으로, 병원 언급은 mentions로.
★중요: hook·offer 텍스트에는 병원·의원 이름을 넣지 마라(이름은 clinic 필드에만). 이름이 든 제목이면 이름을 빼고 마케팅 메시지만 hook에."""


def _call(temperature: float = 0.0) -> Callable[[str, str], str]:
    from sonar_care.config import SETTINGS, get_anthropic_client  # M1 설정 재사용

    client = get_anthropic_client()

    def c(system: str, user: str) -> str:
        m = client.messages.create(model=SETTINGS.judge_model, max_tokens=1500,
                                   system=system, messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in m.content if getattr(b, "type", "") == "text")

    return c


def _parse(raw: str) -> dict:
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1:
        return {"refs": [], "mentions": []}
    try:
        d = json.loads(raw[s : e + 1])
        return {"refs": d.get("refs", []), "mentions": d.get("mentions", [])}
    except json.JSONDecodeError:
        return {"refs": [], "mentions": []}


def extract_blob(text: str, *, call_fn: Callable[[str, str], str] | None = None, max_chars: int = 6000) -> dict:
    call = call_fn or _call()
    return _parse(call(SYS, text[:max_chars]))


def extract_all(*, call_fn: Callable[[str, str], str] | None = None) -> dict:
    """raw/*.txt 전부 추출해 refs·mentions 합산(실명 포함, 인메모리)."""
    refs, mentions = [], []
    for f in sorted(RAW.glob("*.txt")):
        d = extract_blob(f.read_text(encoding="utf-8"), call_fn=call_fn)
        refs.extend(d["refs"])
        mentions.extend(d["mentions"])
    return {"refs": refs, "mentions": mentions}


HYP_SYS = """너는 마케팅 인텔 분석가다. 주어진 경쟁사(익명) 마케팅 레퍼런스에서 '왜 이게 먹히는가' 가설을 3~5개 뽑아 JSON으로만 답하라.
{"hypotheses":[{"clinic":"익명 id","hypothesis":"가설 한 줄","evidence_signals":["이 가설을 지지하는 관찰 신호(레퍼런스에서)"]}]}
반드시 '가설'로만 서술(확정된 인과 아님). 근거는 주어진 레퍼런스에서만."""


def hypotheses(refs_anon: list[dict], *, call_fn: Callable[[str, str], str] | None = None) -> list[dict]:
    if not refs_anon:
        return []
    call = call_fn or _call()
    payload = json.dumps(refs_anon, ensure_ascii=False)[:6000]
    out = _parse_list(call(HYP_SYS, payload))
    return out


def _parse_list(raw: str) -> list[dict]:
    s, e = raw.find("{"), raw.rfind("}")
    if s == -1:
        return []
    try:
        return json.loads(raw[s : e + 1]).get("hypotheses", [])
    except json.JSONDecodeError:
        return []
