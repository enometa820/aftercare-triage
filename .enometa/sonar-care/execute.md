# sonar-care — 실행 로그

> 작성: 2026-07-26 / 단계: execute / 선행 = plan.md / 모드 = ouroboros 자율

## 착수 판정
- **AC-3.3 (가이드라인 RAG)**: M1 회복궤적 KB는 소규모 → RAG는 과설계(BP §D). **skip → M2(Sonar Scan)로 이동** (대규모 크롤 코퍼스가 실재하는 자리). "정당한 자리에 배치" 실천. spec §8.1 해소.

## 실행 진행

### Wave 1 — 스캐폴딩·계약 (메인 직접, 완료)
- **AC-0.1**: `pyproject.toml`(deps: anthropic·pydantic·uqlm·mapie·deepeval·fastapi 등) + `src/sonar_care/__init__.py`
- **AC-0.2**: `src/sonar_care/config.py` — env 키 로드 + Claude/ChatAnthropic 지연 팩토리(키 없이도 import 가능)
- **AC-1.1**: `src/sonar_care/schema.py` — Procedure·Language·Verdict enum + PatientInput·Judgment·TriageResult
- **AC-3.3**: SKIP→M2 (소규모 KB RAG 과설계 회피)
