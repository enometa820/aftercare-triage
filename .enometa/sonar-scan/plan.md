# sonar-scan — 계획 (AC tree)

> 작성: 2026-07-26 / 단계: plan / 선행 = spec.md
> 대상 = Sonar 모듈 2(Sonar Scan). 파이썬 패키지 `sonar_scan`. M1 스택·패턴 재사용.

## AC Tree

- [x] **AC-0**: 스캐폴딩 — `src/sonar_scan/__init__.py` + (M1 pyproject·config·.venv 재사용, 신규 의존 없음)
- [x] **AC-1**: 스키마 — `src/sonar_scan/schema.py` Pydantic: `ClinicSignal`(익명id·소스·리뷰수·평점·언급수·raw텍스트) · `MarketingRef`(hook·offer·channel·category·source) · `SuccessHypothesis`(가설·근거신호·"(가설)"플래그) · `ReputationScore`(익명id·composite·rank·감성분포) · `ScanResult`
- [x] **AC-2**: 수집 — `src/sonar_scan/collect.py` Scrapling으로 공개 소스(네이버 블로그/플레이스 검색·구글 등) 클리닉 마케팅·리뷰 신호 수집→`data/scan/raw/`(gitignore). robots/ToS 준수·PII 미수집. **봇벽 시 확보 가능 소스로 조정 or 라벨된 샘플, 수집 로그에 정직 표기**
- [x] **AC-3**: 익명화 — `src/sonar_scan/anonymize.py` 실명→Clinic A/B/C 결정론 매핑(매핑표 `_local/`, gitignore). 공개 산출물은 익명만
- [x] **AC-4**: 레퍼런스·성공요인 추출 — `src/sonar_scan/extract.py` LLM(주입형)로 광고·프로모션→`MarketingRef` 구조화 + `SuccessHypothesis`("(가설)" 라벨·근거). Pydantic 검증+retry
- [x] **AC-5**: 평판 지수·상대순위 — `src/sonar_scan/reputation.py` 투명 산출식(리뷰수·평점·감성·언급량 가중 합)→composite + 수집셋 내 rank. 산출식 문서화, "공식순위 아님" 명시
- [x] **AC-6**: 감성·토픽 — `src/sonar_scan/sentiment.py` LLM(주입형) 리뷰 감성(긍/부/중)·토픽 집계(PII 0)
- [x] **AC-7**: 대시보드 — `app/scan.py`(+템플릿) 또는 정적 HTML: "경쟁 레퍼런스 + 성공요인 가설 + 우리 상대순위·강약점 토픽" 한 화면. M1 톤
- [x] **AC-8**: eval·정직 테스트 — `eval/test_scan.py` pytest: 익명화 동작·공개 산출물 PII/실명 grep 0·성공요인 "(가설)" 라벨 존재·지수 산출식 결정론 재현. 무키(주입 LLM·캐시 소비)

## 메타

| AC | 의존 | 파일 영역 | 크기 |
|---|---|---|---|
| AC-0 | (없음) | `src/sonar_scan/__init__.py` | 작음 |
| AC-1 | AC-0 | `src/sonar_scan/schema.py` | 작음 |
| AC-2 | AC-1 | `src/sonar_scan/collect.py`·`data/scan/raw/` | 큼 |
| AC-3 | AC-1 | `src/sonar_scan/anonymize.py` | 작음 |
| AC-4 | AC-1·AC-2 | `src/sonar_scan/extract.py` | 큼 |
| AC-5 | AC-1·AC-2·AC-3 | `src/sonar_scan/reputation.py` | 중간 |
| AC-6 | AC-1·AC-2 | `src/sonar_scan/sentiment.py` | 중간 |
| AC-7 | AC-4·AC-5·AC-6 | `app/scan.py`·템플릿 | 큼 |
| AC-8 | AC-3·AC-5·AC-7 | `eval/test_scan.py` | 중간 |

## 실행 가이드
- 1차: AC-0→AC-1(계약). 2차: AC-2(수집, 봇벽 실측)·AC-3(익명화) 병렬 가능(파일 다름).
- 3차: AC-4·AC-6(추출·감성, 둘 다 extract 계열이나 파일 다르면 병렬)·AC-5(지수).
- 4차: AC-7(대시보드)·AC-8(테스트).
- 큰 AC(AC-2·4·7) subagent 가능. 단 AC-2 수집은 봇벽·ToS 판단이 필요해 메인이 직접 착수 후 결과 보고.
- **AC-2 착수 판정**: 공개 소스 봇벽을 Scrapling 정적으로 먼저 실측 → 되면 실수집, 막히면 확보 소스 조정 or 라벨 샘플(정직 표기). execute.md에 1줄 기록.
