# sonar-care — 계획 (AC tree)

> 작성: 2026-07-26 / 단계: plan / 선행 = spec.md(승인)
> 대상 = Sonar 모듈 1(Sonar Care). 파이썬 패키지 `sonar_care`.

## AC Tree

- [ ] **AC-0**: 프로젝트 스캐폴딩 + 설정
  - [ ] **AC-0.1**: `pyproject.toml`(또는 `requirements.txt`) 신설 — anthropic·pydantic>=2·uqlm·mapie·deepeval·fastapi·jinja2·pyyaml·numpy·matplotlib 명시 + `src/sonar_care/__init__.py` 패키지 골격
  - [ ] **AC-0.2**: `src/sonar_care/config.py` — env(vault)에서 API 키 로드 + Claude 클라이언트 팩토리(uqlm용 LangChain `ChatAnthropic` 래퍼 포함)
- [ ] **AC-1**: 입력·출력 스키마 (spec §3.1·3.4)
  - [ ] **AC-1.1**: `src/sonar_care/schema.py` — Pydantic `PatientInput`(증상 텍스트, 사진경로 optional, 시술종류 `Literal["쌍꺼풀","코성형","필러"]`, 경과일 int, 언어) + `Verdict`(verdict `Literal["정상","불확실","레드플래그"]`, reasons[], kb_refs[], red_flag_matched[])
- [ ] **AC-2**: 레드플래그 룰 우선 (spec §3.2)
  - [ ] **AC-2.1**: `data/redflags/ko.yaml`·`ja.yaml` — 시술별 응급 신호 사전(발열·번지는 발적·화농·극심통증·호흡곤란·시야변화·필러 후 피부색변화/극심통증=혈관폐색 등)
  - [ ] **AC-2.2**: `src/sonar_care/redflags.py` — 언어 감지 → 사전 매칭 → 매칭 시 `red_flag_matched` 반환(이후 LLM 판정과 무관하게 레드플래그 강제)
- [ ] **AC-3**: KB 그라운딩 (spec §3.3)
  - [ ] **AC-3.1**: `data/kb/recovery/{쌍꺼풀,코성형,필러}.yaml` — 시술별 정상 회복궤적(경과일 구간별 정상 범위) + 공개 출처 인용 필드
  - [ ] **AC-3.2**: `src/sonar_care/kb.py` — 시술·경과일로 해당 블록 라우팅해 full-context 문자열 + 항목 ID 반환
  - [ ] **AC-3.3**: `src/sonar_care/rag.py` + `data/kb/guidelines/` — 공개 의료 애프터케어 가이드라인 코퍼스 수집 + OSS 임베딩 벡터DB 인덱싱 + 검색·인용 반환 (코퍼스 규모 판단은 execute 착수 시 1줄 확정 — 부족하면 M2로 이동하고 본 AC skip 표기)
- [ ] **AC-4**: 판정 — 구조화 출력 (spec §3.4)
  - [ ] **AC-4.1**: `src/sonar_care/judge.py` — Claude 호출 + 시스템프롬프트(진단·처방 금지·권위 무력화) + KB/RAG 컨텍스트 주입 + Pydantic `Verdict` 검증·실패 시 retry
- [ ] **AC-5**: 불확실성 기권 게이트 (spec §3.5)
  - [ ] **AC-5.1**: `src/sonar_care/gate.py` — uqlm `BlackBoxUQ`(self-consistency, num_responses 5~10)로 confidence 산출 + `abstain` 결정 인터페이스
  - [ ] **AC-5.2**: `eval/calibrate.py` — 라벨 캘리브레이션셋으로 split conformal 임계값 산출(MAPIE), 가능 시 레드플래그 FNR 상한(CRC)
- [ ] **AC-6**: 이미지 defer-by-default (spec §3.6)
  - [ ] **AC-6.1**: `judge.py` VLM 경로 — 사진 self-consistency + 저신뢰/저품질 시 자동 기권, 텍스트·이미지 비대칭 융합(둘 다 고신뢰만 "정상")
- [ ] **AC-7**: 파이프라인 + 다국어 에스컬레이션 (spec §3.7)
  - [ ] **AC-7.1**: `src/sonar_care/triage.py` — 오케스트레이션(입력→redflags→kb/rag→judge→gate→3-way 출력)
  - [ ] **AC-7.2**: `src/sonar_care/escalation.py` — 레드플래그 시 구조화·번역(한↔일) 클리닉용 요약 생성
- [ ] **AC-8**: 평가셋 + eval 하네스 (spec §3.8)
  - [ ] **AC-8.1**: `data/eval/cases.jsonl` — ~90건(쌍꺼풀·코성형·필러 × 정상/불확실/레드플래그 × ~10, 경계 집중, 한+일) + 라벨(가이드라인/룰 유래 + 멀티모델 합의 + 10% 사람 스팟체크 기록)
  - [ ] **AC-8.2**: `eval/test_triage.py` — DeepEval pytest, 레드플래그 recall 게이트(임계 미달 시 exit non-zero) + 클래스별 precision/recall
  - [ ] **AC-8.3**: `eval/promptfoo.yaml` — 권위 사칭·멀티턴·응급 오도 적대 스위트
- [ ] **AC-9**: 측정·시각화 (spec §3.9)
  - [ ] **AC-9.1**: `eval/rc_curve.py` — 게이트 A(무게이트) vs B(게이트) Risk-Coverage 곡선 + 레드플래그 FNR + ECE (matplotlib 이미지 산출)
- [ ] **AC-10**: 데모 UI (spec §3.10)
  - [ ] **AC-10.1**: `app/main.py` + `app/templates/` — FastAPI + HTMX 1페이지(입력→판정/안심·에스컬 + 게이트 A/B 패널), 일본어 입력→한국어 에스컬 요약 시연 케이스 1건 프리셋

## 메타

| AC | 의존 | 파일 영역 | 크기 |
|---|---|---|---|
| AC-0.1 | (없음) | `pyproject.toml`·`src/sonar_care/__init__.py` | 작음 |
| AC-0.2 | AC-0.1 | `src/sonar_care/config.py` | 작음 |
| AC-1.1 | AC-0.1 | `src/sonar_care/schema.py` | 작음 |
| AC-2.1 | (없음) | `data/redflags/ko.yaml`·`ja.yaml` | 중간 |
| AC-2.2 | AC-1.1·AC-2.1 | `src/sonar_care/redflags.py` | 작음 |
| AC-3.1 | (없음) | `data/kb/recovery/*.yaml` | 중간 |
| AC-3.2 | AC-3.1 | `src/sonar_care/kb.py` | 작음 |
| AC-3.3 | AC-0.2 | `src/sonar_care/rag.py`·`data/kb/guidelines/` | 큼 |
| AC-4.1 | AC-1.1·AC-3.2 | `src/sonar_care/judge.py` | 큼 |
| AC-5.1 | AC-4.1 | `src/sonar_care/gate.py` | 중간 |
| AC-5.2 | AC-5.1·AC-8.1 | `eval/calibrate.py` | 중간 |
| AC-6.1 | AC-4.1 | `src/sonar_care/judge.py` | 중간 |
| AC-7.1 | AC-2.2·AC-3.2·AC-4.1·AC-5.1·AC-6.1 | `src/sonar_care/triage.py` | 중간 |
| AC-7.2 | AC-4.1 | `src/sonar_care/escalation.py` | 중간 |
| AC-8.1 | AC-1.1 | `data/eval/cases.jsonl` | 큼 |
| AC-8.2 | AC-7.1·AC-8.1 | `eval/test_triage.py` | 중간 |
| AC-8.3 | AC-7.1 | `eval/promptfoo.yaml` | 작음 |
| AC-9.1 | AC-5.2·AC-8.1 | `eval/rc_curve.py` | 중간 |
| AC-10.1 | AC-7.1·AC-9.1 | `app/main.py`·`app/templates/` | 큼 |

## 실행 가이드 (/enometa-execute 참조)

- **1차(독립·병렬 가능, 파일 겹침 0)**: AC-0.1 → 그 후 AC-2.1·AC-3.1·AC-8.1(데이터 3종, 서로 독립)·AC-1.1 병렬.
- **2차**: AC-0.2, AC-2.2, AC-3.2 (작음, 메인 Claude 직접).
- **3차(큼 = subagent 권장)**: AC-3.3(RAG), AC-4.1(judge) — 단 둘 다 `judge.py`/`rag.py`로 파일 다르니 병렬 가능. AC-4.1이 AC-6.1과 같은 `judge.py` → **AC-4.1과 AC-6.1은 순차**(파일 겹침).
- **4차**: AC-5.1 → AC-5.2·AC-6.1 → AC-7.1(파이프라인 통합)·AC-7.2.
- **5차**: AC-8.2·AC-8.3 → AC-9.1 → AC-10.1(데모, 큼 = subagent).
- 큰 AC(AC-3.3·AC-4.1·AC-8.1·AC-10.1) = general-purpose subagent 디스패치 권장. 나머지 작음·중간 = 메인 직접.
- **AC-3.3 조건부**: execute 착수 시 가이드라인 코퍼스 규모를 1줄로 판정 — 충분히 크면 진행, 아니면 skip하고 M2 spec으로 이동 표기(spec §8.1).
