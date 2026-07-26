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

### Wave 2 — 데이터·독립 모듈 (subagent 병렬 3개, 완료)
- **AC-2.1/2.2** (ac2-redflags): `data/redflags/{ko,ja}.yaml`(룰 16개, 공통6+시술별, 필러 혈관폐색 응급) + `redflags.py` `match_redflags()`. 출처 실인용.
- **AC-3.1/3.2** (ac3-kb): `data/kb/recovery/{쌍꺼풀,코성형,필러}.yaml`(구간별 정상궤적+watch) + `kb.py` `route_kb()`. 출처=2차자료 위주(업그레이드 권장 주석).
- **AC-8.1** (ac8-evalset): `data/eval/cases.jsonl` 90건(30/30/30, ko:ja 63:27, boundary 48) + `LABELING.md`(3겹 방어). 전부 합성 명시.
- venv 현황: pydantic·pyyaml만 설치됨 → Wave 3서 anthropic·langchain-anthropic·mapie·numpy·matplotlib(+uqlm 시도) 설치.

### Wave 3 — LLM 코어 (메인 직접, 완료)
- **AC-4.1** `judge.py`: Claude 구조화 판정(진단금지·권위무력화 시스템프롬프트) + Pydantic 검증·retry, 파싱 2회 실패 시 보수적 불확실. call_fn 주입형(무키 테스트).
- **AC-5.1** `gate.py`: self-consistency k회 빈도 confidence + 비대칭(레드플래그 red_min=2표로 채택, 정상은 threshold 이상만) + 기권. uqlm은 대체재로 문서화(torch 회피, 네이티브 구현).
- **AC-6.1** `judge.py` 이미지: 사진 첨부 + defer-by-default(애매하면 표 갈려 confidence↓→기권), 정확도 주장 안 함.
- **AC-7.1** `triage.py`: rules-first→KB 라우팅→게이트→3-way 오케스트레이션. **AC-7.2** `escalation.py`: 다국어 에스컬/안심(무키 템플릿 폴백).
- **오프라인 스모크 5/5 통과**(주입 판정): 룰 short-circuit·정상·기권·게이트 레드플래그(2/7)·일본어 에스컬.
- **실 Claude 검증 통과**(vault 키·claude-sonnet-5): 코성형 5일→정상+안심, 쌍꺼풀 21일 악화→레드플래그+에스컬. ★claude-sonnet-5는 `temperature` 폐기 → 호출서 제거(self-consistency는 기본 샘플링 변동으로 성립).
