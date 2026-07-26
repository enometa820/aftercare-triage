# sonar-scan — 실행 로그

> 2026-07-26 / 단계: execute / 선행 = plan.md / 모드 = 자율

## 착수 판정 (AC-2)
- Scrapling 정적 실측: **네이버 통합검색(view)은 실크롤됨**(코성형 후기 16.8k 등). 구글·네이버맵은 봇벽(0~97자) → 미사용(ToS 준수·우회 안 함). → 네이버 view를 1차 소스로 확정.

## 실행 진행 (전 AC 완료)
- **AC-0/1**: `sonar_scan` 패키지 + `schema.py`(ClinicSignal·MarketingRef·SuccessHypothesis·ReputationScore·ScanResult). M1 pyproject·venv 재사용.
- **AC-2 수집**: `collect.py` 네이버 view 5질의 실크롤 5/5(8~17k자) → `data/scan/raw/`(gitignore). 봇벽·PII 정직 로그.
- **AC-3 익명화**: `anonymize.py` 실명→Clinic A/B/C 결정론 매핑(`_local/scan_anon_map.json` gitignore) + `scrub()` 자유텍스트 실명 치환(방어 심층화). **공개 산출물 실명 잔존 0 검증.**
- **AC-4 추출**: `extract.py` LLM 광고·후기→MarketingRef + mentions(감성). hook에 병원명 배제 강제. + `hypotheses()` 성공요인 "(가설)" 라벨·근거.
- **AC-5 평판**: `reputation.py` 투명 산출식(0.6·언급정규화 + 0.4·감성) composite + 수집셋 내 rank. FORMULA 공개, "공식순위 아님" 명시.
- **AC-6 감성**: 추출에 통합(mentions sentiment 긍/중/부).
- **AC-7 대시보드**: `report.py` → `docs/scan-dashboard.html`(자체완결·CDN 0): 레퍼런스·성공요인 가설·평판 상대순위·감성 + 정직 노트.
- **AC-8 테스트**: `eval_scan/test_scan.py` pytest 6/6 — 익명화·scrub·평판 결정론·추출 오프라인·가설 라벨·**공개 실명 잔존 0**·투명성 노트.
- 러너: `eval_scan/run_scan.py`(실 LLM 추출·가설) → 익명 `data/scan/scan_result.json` 커밋본.

## 실측 결과 (정직)
- 클리닉 11·레퍼런스 13·성공요인 가설 5. 레퍼런스·가설은 실제 마케팅 신호에서 구조화(refradar 재현 실동작).
- **평판 지수 한계**: 공개 블로그 언급이 클리닉당 대부분 1건이라(언급 2건+ 0/11) 지수 변별력 약함(다수 동점) → 리뷰수·평점 등 신호 보강 필요. M1과 같은 정직 발견: 강한 산출물은 레퍼런스·가설, 지수는 신호 보강 시 의미. 대시보드·docs에 명시.
- 안전: 공개 실명 잔존 0, 리뷰어 PII 0, 성공요인=가설, 순위=투명지수(공식 아님).

## 완료 → verify
