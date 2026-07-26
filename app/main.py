"""Sonar Care 데모 — FastAPI 1페이지 웹(AC-10).

- 환자 입력 → triage → 판정/안심·에스컬레이션. 옆에 '측정된 안전' 패널(A/B RC 곡선·지표).
- /api/triage (JSON) = promptfoo 등 프로그램 호출용. / = 데모 페이지.
- 실 판정은 Claude 키가 필요 — 시작 시 env→vault 순으로 로드.
실행: .venv/Scripts/python.exe -m uvicorn app.main:app --reload  (http://localhost:8000)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _ensure_key() -> None:
    if os.getenv("ANTHROPIC_API_KEY"):
        return
    vault = Path.home() / ".vault" / "enometa-distill" / ".env.local"
    if vault.exists():
        m = re.search(r"^ANTHROPIC_API_KEY=(.+)$", vault.read_text(encoding="utf-8"), re.M)
        if m:
            os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip().strip('"').strip("'")


_ensure_key()

from sonar_care.config import has_api_key  # noqa: E402
from sonar_care.schema import Language, PatientInput, Procedure  # noqa: E402
from sonar_care.triage import triage  # noqa: E402

app = FastAPI(title="Sonar Care — 측정된 안전 사후케어 트리아지")
DOCS = ROOT / "docs"
if DOCS.exists():
    app.mount("/assets", StaticFiles(directory=str(DOCS)), name="assets")

TEMPLATE = (ROOT / "app" / "templates" / "index.html").read_text(encoding="utf-8")


class TriageRequest(BaseModel):
    symptom_text: str
    procedure: str = "필러"
    days_since: int = 1
    language: str = "ko"


def _metrics_summary() -> dict:
    p = DOCS / "metrics.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8")).get("summary", {})
    return {}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    summ = _metrics_summary()
    return TEMPLATE.replace("{{METRICS}}", json.dumps(summ, ensure_ascii=False)).replace(
        "{{HASKEY}}", "true" if has_api_key() else "false"
    )


@app.post("/api/triage")
def api_triage(req: TriageRequest) -> JSONResponse:
    if not has_api_key():
        return JSONResponse({"error": "ANTHROPIC_API_KEY 없음 — vault/env 확인"}, status_code=503)
    inp = PatientInput(
        symptom_text=req.symptom_text,
        procedure=Procedure(req.procedure),
        days_since=req.days_since,
        language=Language(req.language),
    )
    r = triage(inp)
    return JSONResponse(
        {
            "verdict": r.verdict.value,
            "confidence": round(r.confidence, 2),
            "abstained": r.abstained,
            "reasons": r.reasons,
            "kb_refs": r.kb_refs,
            "red_flag_matched": r.red_flag_matched,
            "reassurance": r.reassurance,
            "escalation_summary": r.escalation_summary,
        }
    )
