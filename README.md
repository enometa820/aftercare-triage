# Sonar (소나) — 성형·피부 클리닉 2축 AI 시스템

> "표면 아래 신호를 감지한다." (repo 작업명 `aftercare-triage`)
>
> - **Sonar Care (모듈 1) — 술후 안전 트리아지:** 회복기 환자를 텍스트+사진으로 받아 정상 경과는 다국어 안심, 불확실·이상징후는 **기권(defer)해 의사에게 에스컬레이션.** 명제 = **"AI 정확도가 아니라, 못 믿을 때를 알고 사람에게 넘기는 능력"(측정된 안전).**
> - **Sonar Scan (모듈 2) — 마케팅·평판 인텔:** 공개 신호를 크롤해 경쟁사 마케팅 레퍼런스·성공요인 가설·우리 병원 평판/상대순위를 뽑는다.
> - **통합:** 사후케어↑ → 평판↑ → 신규유치↑ (MSO 루프).

이 저장소는 결과물뿐 아니라 **문제를 정의하고 좁혀 만든 과정 전체**를 담는다 — 기획력·조사력·실행력·구현력을 과정으로 보여주기 위해.

## 왜 이 문제인가

성형·피부 의료는 **크로스보더(특히 한일)**로 커지는데, 환자가 시술 후 귀국하면 회복기 관리가 거리·시차·언어로 끊긴다. 조사해 보니 국제적으로도 **미용 × 크로스보더 × 사진 × 안전 트리아지**를 함께 다루는 제품은 비어 있었다(강남언니/UNNI조차 발견·예약에서 멈춤). 동시에 논문 실측으로 **범용 VLM 상처판정 정확도 62~72%, LLM이 위험할 때 기권하는 recall 13%** — 즉 날것 모델은 임상급이 아니고, **진짜 자산은 모델이 아니라 안전 게이트(평가셋·가드레일·불확실성 기권)**다.

## 접근 — 측정된 안전

```
입력: 증상 텍스트 + 회복 사진 + (시술종류 · 경과일)
  → LLM+VLM 융합 판정 → 불확실성 게이트
    ① 정상(고확신)  → 다국어 안심 + 자가관리 안내
    ② 불확실         → 기권 → 의사 에스컬레이션
    ③ 레드플래그     → 즉시 에스컬레이션(구조화·번역 요약)
```

- **멀티모달, 단 사진은 "맹신하지 않는다".** VLM 약점을 숨기지 않고 불확실성 게이트로 흡수한다.
- **AI는 진단·처방을 하지 않는다.** 안심·안내 + 이상징후 triage + 에스컬레이션까지. 의료 안전선을 설계로 지킨다.
- **데모의 심장은 측정.** 게이트 유무에 따른 기권 precision/recall·위험 오판 감소를 수치·곡선으로 보인다.

## 문서 지도

- [`기획.md`](기획.md) — 컨셉·설계 결정·정직성 가드·데모 계획·로드맵 (SSOT)
- [`여정-기록.md`](여정-기록.md) — 최초 기획부터의 사고 과정(문제를 어떻게 좁혔나)
- [`조사-시장과-기술.md`](조사-시장과-기술.md) — 국제 제품 지형 gap + 기술 프런티어 SOTA (출처 포함)
- [`BP-기술-베스트프랙티스.md`](BP-기술-베스트프랙티스.md) — 구현 기술 베스트프랙티스 (불확실성·기권·가드레일·eval)
- [`조사-참고구현.md`](조사-참고구현.md) — 재사용 자산 카탈로그(uqlm·MAPIE·DeepEval 등, Scrapling 크롤 추출)

## 상태

M1(Sonar Care)·M2(Sonar Scan) **구현·우로보로스 verify 완료**(각 spec→plan→execute→verify, `.enometa/` 트레일 공개). 다음 = 피치덱.

## QUICKSTART (5분)

```bash
git clone https://github.com/enometa820/sonar   # (구 aftercare-triage)
cd sonar
uv venv .venv && uv pip install --python .venv -e .        # core deps
# 판정 LLM을 쓰려면 키 필요(데모/실행):  export ANTHROPIC_API_KEY=...

# 테스트(무키·결정론) — M1+M2 전체
.venv/Scripts/python -m pytest eval/test_triage.py eval_scan/test_scan.py -q

# M1 데모(웹, 키 필요): http://localhost:8000
.venv/Scripts/python -m uvicorn app.main:app
# M1 측정 재현(A/B 곡선·ECE): 실측 실행 후 그래프 생성
.venv/Scripts/python eval/run_eval.py --k 5   # (키 필요, results.jsonl)
.venv/Scripts/python eval/rc_curve.py         # docs/measured-safety.png

# M2 인텔 재현: 네이버 view 실크롤 → 익명 인텔 → 대시보드
.venv/Scripts/python eval_scan/run_scan.py    # (키 필요) data/scan/scan_result.json
.venv/Scripts/python -c "import sys;sys.path.insert(0,'src');from sonar_scan.report import build;build()"  # docs/scan-dashboard.html
```
무키에서도 pytest(주입 LLM·캐시 소비)·대시보드 렌더는 동작. 실 판정·크롤만 키·네트워크 필요.

## 정직성

데모 데이터는 **합성·공개출처**이며 실제 환자 데이터가 아니다. 이 저장소가 증명하는 것은 임상 성능이 아니라 **안전 게이트가 위험을 측정 가능하게 줄인다는 방법론**이다.

---
설계·구현: 이용진 (AI Automation Engineer)
