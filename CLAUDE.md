# CLAUDE.md — aftercare-triage

이 파일은 Claude Code가 이 저장소에서 작업할 때의 가이드다. 새 세션은 이 파일 → [`기획.md`] 순으로 읽으면 매끄럽게 이어진다.

north star: 모아씨앤씨의 성형·피부 크로스보더 사후케어 문제를 겨냥한 AI 프로덕트 모듈 — 이용진의 AI Automation Engineer 포트폴리오 자산. (어필 맥락 등 내부 메모 = `_local/전략.md`, 공개 제외.)

## 이 프로젝트가 뭔가

**Sonar(소나)** — 성형·피부 크로스보더 클리닉용 **2축 AI 시스템** (순차 빌드, "표면 아래 신호를 감지한다"): **모듈 1 = Sonar Care = 술후 안전 트리아지**(환자 텍스트+사진 → 정상은 다국어 안심 / 불확실·이상징후는 기권→의사 에스컬레이션, 명제 = "AI 정확도가 아니라 *못 믿을 때 사람에게 넘기는 능력*", 측정된 안전) + **모듈 2 = Sonar Scan = 마케팅·평판 인텔**(Scrapling 크롤 → 경쟁 마케팅 레퍼런스·성공요인 가설·평판/상대순위, refradar 재현). 통합 = MSO 루프(사후케어→평판→유치). **M1 먼저 완결 → M2**, 각 축 단일기능.

이건 단순 챗봇이 아니라 **기획력·조사력·실행력·구현력을 통째로 보여주는 어필 자산**이다 — 그래서 최초 기획부터의 **과정 자체를 기록**([`여정-기록.md`])하고, 최종 산출은 SVG 다이어그램·설계 지도가 들어간 **HTML 피치덱 + 작동 데모**다.

## 문서 지도 (루트 = 단일 진입점, 재사용 정본)

- [`기획.md`] — **SSOT.** 컨셉·확정 결정(decision log)·정직성 가드·데모 계획·로드맵·열린 질문. 무엇을·왜·어떻게의 정본.
- [`여정-기록.md`] — 최초 기획부터의 과정 서사(grill 여정). 피치덱 서사의 원천.
- [`조사-회사-모아씨앤씨.md`] — 대상 회사 전면조사(근거). ⚠️ PII·민감정보 포함 — 공개 저장소 반입 전 정제 필요(아래 "공개 주의").
- [`조사-시장과-기술.md`] — 국제 제품 지형 gap + 기술 프런티어 SOTA(출처 URL).
- [`BP-기술-베스트프랙티스.md`] — 구현 기술 베스트프랙티스(심화조사, 재사용). 코드 짜기 전 참조.
- [`조사-참고구현.md`] — 재사용 자산 카탈로그(uqlm·MAPIE·DeepEval 등). 크롤러 = `refs/crawl.py`(Scrapling), 원본 = `refs/raw/`(gitignore 로컬).

## 핵심 설계 (코드 바꾸기 전 반드시 이해)

- **자산은 모델이 아니라 게이트다.** raw VLM 정확도 62~72%·abstention recall 13%(논문 실측). 진짜 해자 = 평가셋·가드레일·불확실성 게이트. 정확도 자랑 금지, "못 믿을 때 기권" 증명.
- **멀티모달(텍스트+사진) 둘 다 1급 입력.** 단 사진 역할 = "정확 판독"이 아니라 "불확실하면 기권". VLM 약점을 정면 무기화.
- **AI는 진단·처방 0.** 안심·안내 + triage → 에스컬레이션만. 의료법 안전선.
- **측정이 데모의 심장.** 게이트 유무에 따른 abstention precision/recall·위험 오판 감소를 수치·곡선으로.

## 정직성 가드 (절대선)

- 날조·과장·**축소** 금지. 지어낸 수치·가짜 출처·"임상검증" 허위 0.
- **데모 데이터 = 합성·공개출처임을 항상 명시.** 실환자 데이터 아님. 측정 대상 = 게이트 동작(방법론)이지 임상 정확도 아님.
- 기술 주장은 "면접에서 무너지는가"로 판별. 근거 있는 추정은 (추정)/(가정)/(전망) 라벨 + 근거 함께.
- 한국어 산출물 = 한자·전각 0 지향. 배포·공유 전 셀프리뷰.

## 공개 주의 (GitHub)

- `조사-회사-모아씨앤씨.md`는 대상 회사의 PII(사업자번호·대표 개인 연락처)와 약점 티어다운을 담는다. **공개 저장소에 그대로 올리면 안 된다**(PII + "지원자가 우리 약점을 공개함" 역효과). 기본은 gitignore. 공개 레포엔 정제본만.
- 공개 레포의 각도 = **제품·과정·기술(어필)**. 회사별 약점 분석은 로컬/비공개 유지.

## 현재 단계 / 다음

- [x] 전면조사·국제 SOTA 조사, 컨셉 grill 확정, 프로젝트 셋업, 브랜드 Sonar
- [x] **M1 Sonar Care** 구현 + 우로보로스 verify 통과(회차2). `.enometa/sonar-care/`
- [x] **M2 Sonar Scan** 구현 + 우로보로스 verify 통과(회차2). `.enometa/sonar-scan/`
- [x] 마감: QUICKSTART·데모 워크스루 대본·이미지 defer 검증·repo명 sonar rename
- [x] **피치덱** — `docs/pitch.html`(자체완결·다크 소나콘솔, SVG 다이어그램 4종+측정 PNG, 여정·측정·정직 서사)
- [ ] (선택) 피치덱 live 링크(GitHub Pages/Vercel) · M1 이미지 임상 평가셋(consented) · 데모 영상

## 명령

```bash
uv venv .venv && uv pip install --python .venv -e ".[dev]"   # + [research]는 선택
export ANTHROPIC_API_KEY=...   # 실 판정·크롤 시 (vault: enometa-distill/.env.local)
.venv/Scripts/python -m pytest eval/test_triage.py eval_scan/test_scan.py -q   # 무키 16개
.venv/Scripts/python -m uvicorn app.main:app        # M1 데모 :8000
.venv/Scripts/python eval/run_eval.py --k 5 && .venv/Scripts/python eval/rc_curve.py  # M1 측정
.venv/Scripts/python eval_scan/run_scan.py          # M2 크롤·인텔 → scan_result.json
# 자세한 재현 = README QUICKSTART
```

## 우선순위
플랫폼 시스템·안전 제약 유지 → 사용자 명시 지시 → 이 CLAUDE.md → 글로벌 CLAUDE.md 순 해석.
