# sonar-scan — 검증 (3-Phase)

> 2026-07-26 / 단계: verify / 회차 1

## 회차 1

### Phase 1 — 결정론
- ruff(src/sonar_scan·eval_scan): All checks passed
- pytest eval_scan/test_scan.py: 6 passed / 전체(M1+M2) 15 passed
- import: sonar_scan.{schema,collect,extract,anonymize,reputation,report} OK

### Phase 1.5 — eval / 안전 게이트
| 항목 | 판정 | 근거 |
|---|---|---|
| 공개 산출물 실명 잔존 | ✓ 0 | test_no_realname_leak(로컬 맵 11명 vs scan_result.json 잔존 0) |
| 리뷰어 PII | ✓ 0 | 집계·공개 스니펫만, mentions=감성만 |
| 성공요인 가설 라벨 | ✓ | is_hypothesis True 전건, 대시보드 "(가설)" |
| 순위 투명·공식아님 | ✓ | FORMULA 공개 + "공식 순위 재현 아님" |
| 실크롤 실측 | ✓ | 네이버 view 5/5, 구글·맵 봇벽 정직 표기·우회 안 함 |
- 정직 발견: 평판지수는 언급 희소(2건+ 0/11)로 변별 약함 → 레퍼런스·가설이 핵심, 지수는 신호 보강 시 의미. docs·대시보드에 명시(과장 0).

### Phase 2 — 의미론 (spec §3 대조)
| 요구 | 상태 | 근거 |
|---|---|---|
| 1 수집(Scrapling 공개) | ✓ | collect.py 네이버 view 실크롤, raw gitignore |
| 2 레퍼런스 추출 | ✓ | extract.py MarketingRef(hook/offer/channel/category) |
| 3 성공요인 가설 | ✓ | extract.hypotheses "(가설)"·근거, schema is_hypothesis |
| 4 평판 투명지수·상대순위 | ✓ | reputation.py FORMULA + rank, 공식아님 명시 |
| 5 감성·토픽 | ✓ | mentions sentiment 긍/중/부 집계 |
| 6 익명화·PII가드 | ✓ | anonymize map+scrub, 공개 실명 0, 매핑 로컬 gitignore |
| 7 대시보드 | ✓ | report.py→docs/scan-dashboard.html 자체완결 |
| 8 정직·재현 로그 | ✓ | collection_note·FORMULA·가설라벨, test로 검증 |
성공기준 5/5: 실수집·레퍼런스/가설·평판지수·대시보드·정직안전 가드.

### Phase 2.5 — BP
- refradar(광고 레퍼런스 대량수집) 방법 재조준 ✓ / Scrapling 정적 스텔스(참고구현) ✓ / 정직가드(가설·PII0·투명지수·익명) ✓ / 봇벽 우회 안 함(ToS) ✓

### 외부 자산 점검
- `docs/scan-dashboard.html` = 공개 대시보드지만 익명(Clinic A/B/C)·리뷰어 PII 0·실명 잔존 0(test) → 공개 안전. 실명↔익명 매핑은 `_local/`(gitignore).

### Phase 3 — Adversarial subagent
(verify-adv-scan 디스패치 — 결과 도착 시 갱신)

### Phase 3 — Adversarial (회차1, verify-adv-scan 격리)
판정 = 실패. 안전·정직 코어(실명0·PII0·가설표기·투명지수·봇벽우회 없음)는 grep으로 클린 확인. 실패 사유 = 완전성 결함 3건:
- §3-5 토픽 추출 전무(감성만) · §3-7 대시보드 강약점 토픽 없음 · §3-8 수집시각 부재 · (부수) ClinicSignal 미사용 흔적.
스코프 이탈·PII/날조 누수 = 없음.

## 회차 2 — 완전성 갭 수정
| 갭 | 수정 | 근거 |
|---|---|---|
| 토픽 추출(§3-5) | extract mentions에 topics 추가 + reputation top_topics·topic_summary 집계 | test_topics_and_timestamp ✓ |
| 강약점 토픽(§3-7) | 대시보드 토픽 칩·클리닉별 top_topics 칼럼·우리병원 강조 | report.py, scan-dashboard.html |
| 수집시각(§3-8) | ScanResult.collected_at(tz-aware) | scan_result.json collected_at |
| ClinicSignal 흔적 | 미사용 스키마 제거 | schema.py |
- Phase 1 재실행: ruff All passed / pytest 16/16(M1 9+M2 7) / 실 재실행(토픽·시각 산출 확인).
- 안전·정직 가드는 회차1에서 이미 클린 판정 → 미변경(실명0·PII0·가설·투명지수 유지).

## 종합 판정 — 회차 2: **통과 ✅**
객관 완전성 갭 3건 닫힘(테스트 고정) + 안전·정직 클린 유지. 우로보로스 sonar-scan(M2) 사이클 완료.
- 성공기준 5/5. 정직: 평판지수 언급 희소 한계·our_clinic 플레이스홀더를 데이터·문서에 그대로 표기(과장 0).
