# sonar-care — 검증 (3-Phase)

> 작성: 2026-07-26 / 단계: verify / 회차 1

## 회차 1 (2026-07-26)

### Phase 1 — 결정론
| 명령 | 결과 |
|---|---|
| `ruff check src eval app` | ✓ All checks passed (초기 22건 → 20 자동수정 + 2 수동정리) |
| `pytest eval/test_triage.py` | ✓ 6 passed |
| 전체 import (8개 모듈) | ✓ import OK |
| 한자 스캔(한국어 산출물) | ✓ 6 hit 전부 의도된 일본어(ja 출력·스모크·프리셋) — 스트레이 한자 0 |
| 데모 스모크(TestClient) | ✓ GET / 200, 실 /api/triage 정상 판정 |

### Phase 1.5 — eval
| 지표 | 판정선 | 이번(실측 18건) | 판정 |
|---|---|---|---|
| 놓친 레드플래그(FNR) | 0건 허용(CI 게이트) | 0건 (A·B 모두) | ✓ |
| 레드플래그 recall | = 1.0 | 1.0 | ✓ |
| 게이트 coverage | (보고) | 0.833 | — |
| 답한 것 정확도 | (보고) | 0.733 | — |
- 실 Claude 실행(`run_eval.py`, 층화 서브셋 18×k5) → `results.jsonl` → `metrics.json`. baseline 개념 = 게이트 없음(A) 대비 게이트(B). 정직: n 작아 통계적 보장 아닌 경험적 측정, 전체 90건 재현 가능.
- failure taxonomy: 모델이 경계(불확실) 케이스를 안전 쪽(레드플래그)으로 과분류 경향 관찰 → 데이터·프롬프트 개선 입력으로 기록(과장 없이).

### Phase 2 — 의미론 (spec §3 대조)
| 요구 | 상태 | 근거 |
|---|---|---|
| 1 입력 | ✓ | `schema.py` PatientInput(증상·사진·시술 enum·경과일·언어) |
| 2 rules-first | ✓ | `triage.py:36` match_redflags 최우선 → 매칭 시 short-circuit 레드플래그(LLM 앞단) |
| 3 KB 그라운딩 | ✓ | `kb.py` route_kb full-context+id, `judge.py` 컨텍스트 주입·인용 강제. RAG는 M2 이동(execute.md 판정) |
| 4 판정 구조화 | ✓ | `judge.py` Pydantic Judgment 검증+retry, SYSTEM_PROMPT 진단·처방·권위무력화 강제 |
| 5 기권 게이트 | ✓ | `gate.py` self-consistency 빈도 + abstain, `calibrate.py` 컨포멀 임계값 |
| 6 이미지 defer | ✓ | `judge.py:44` 사진 첨부·보조신호 명시, `gate.py` 비대칭 융합(정상은 고확신만) |
| 7 3-way+다국어 에스컬 | ✓ | `triage.py` 3-way 분기, `escalation.py` 한↔일 구조화 요약 |
| 8 평가셋+eval CI | ✓ | `cases.jsonl` 90건+`LABELING.md`, `test_triage.py` 레드플래그 recall CI 게이트, `promptfoo.yaml` 적대 |
| 9 측정 A/B | ✓ | `rc_curve.py`+`metrics.py`→`docs/measured-safety.png`·`metrics.json`(실측) |
| 10 데모 UI | ✓ | `app/main.py`+`templates/index.html` FastAPI 1페이지, TestClient 스모크 통과 |

성공기준 5개: 파이프라인 작동 ✓ / 게이트 A/B 곡선 ✓ / 일본어 시연 ✓(프리셋+실검증) / eval CI 통과 ✓ / 웹 데모 ✓.

### Phase 2.5 — BP 체크리스트 (spec §9)
| BP 항목 | 결과 | 근거·비고 |
|---|---|---|
| 명시적 abstain 1급(MedAbstain) | ✓ | gate.py abstain 반환·불확실 매핑 |
| self-consistency 불확실성(uqlm) | ✓ (대체) | 네이티브 빈도 구현 — uqlm(torch/NLI)은 데모 과설계라 대체·문서화. 원리 충족 |
| 컨포멀 FNR 상한(MAPIE CRC) | ✓ (대체) | calibrate.py CRC 원리 직접 구현. n 작음 caveat 명시. MAPIE 등가 |
| rules-first+권위무력화(Red-Teaming) | ✓ | redflags.py 앞단 + SYSTEM_PROMPT 자격주장 불변 + promptfoo 권위사칭 케이스 |
| exact-match 결정론 채점(judge 불안정) | ✓ | test_triage.py exact-match, judge-as-metric 회피 |
| 자동 eval CI(DeepEval/promptfoo) | ✓ (대체) | plain pytest 게이트(BP "이산=exact-match 1순위" 정합) + promptfoo.yaml. DeepEval 무거워 pytest로 |
| 구조화 출력+단일호출(Anthropic) | ✓ | Pydantic enum+retry, 멀티에이전트 배제(단일 호출+라우팅) |
| VLM 저정확도→defer(62~72%) | ✓ | 이미지 정확도 주장 안 함, defer-by-default |
- 정직 표기: uqlm·MAPIE·DeepEval을 네이티브/경량 대체로 구현한 것은 "심플함 우선·데모 과설계 회피"의 문서화된 엔지니어링 판단(원리·BP 정합 유지). 라이브러리 이름을 산출물에 허위로 주장하지 않음.

### 외부 자산 점검
| 항목 | 결과 | 근거 |
|---|---|---|
| 산출물 타입 | 내부(코드·데이터·dev 데모) | LP/공유PDF 아님 → 외부 자산 정밀점검 skip(통과) |
| PII·회사약점 격리 | ✓ | `조사-회사-모아씨앤씨.md`·`_local/` gitignore, 공개 레포엔 미반입 |
| 공개 문서 정제 | ✓ | 개인정보(고졸·경력)·전술 프레이밍은 `_local/전략.md`로 분리(이전 커밋) |

### Phase 3 — Adversarial subagent
(verify-adv 디스패치됨 — 격리 컨텍스트에서 spec §3 대 git diff 대조 진행 중. 결과 도착 시 아래 갱신)
