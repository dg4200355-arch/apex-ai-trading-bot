# APEX Autonomous Validation v9.1

한국·미국 주식을 대상으로 **후보를 많이 만드는 것보다 가짜 후보와 백테스트 착시를 탈락시키는 것**에 초점을 둔 연구·모의투자 시스템입니다.

> 실제 증권사 주문을 전송하지 않습니다. 모든 주문/체결은 shadow paper simulation이며 미래 수익을 보장하지 않습니다.

## ① FULL80 1차 자동검증
- 한국 40 + 미국 40 = 80종목 전체 검사
- 추세 / 반전 / 돌파 / AI 전략 경쟁
- 신호 확정 후 다음 거래일 시가 체결 기준
- 거래비용 반영
- 75% 학습/선택 경계 앞 **5거래일 purge/embargo** 적용
- AI TimeSeriesSplit에도 future gap 적용
- 최종 TEST는 전략/파라미터 선택 후에만 평가
- timing permutation/circular test + BH 다중검정 family size 80
- 전략 종류·정확한 파라미터·데이터 시작/종료일을 동결 저장
- 조정 OHLCV 무결성 검사와 제한적인 고립 High/Low 보정
- 진짜 데이터/엔진 오류가 하나라도 생기면 **fail-closed**: 새 결과로 후보를 제거하지 않고 이전 정상 리포트를 유지

## ② 완전 동결 2차 확인
1차에서 저장된 전략과 파라미터를 그대로 사용하며 다시 최적화하지 않습니다.

- 1차와 동일한 **75% 경계 + 5-bar purge/embargo** 재현
- 1차 TEST 수익 재현오차 검사
- 거래비용 3단계 스트레스
- 주변 파라미터 흔들기
- 동일 파라미터 10년 구간 스트레스
- 처리/데이터 오류 발생 시 stage 전체 fail-closed

## ③ 전진 모의검증
2차 확인후보만 고정 전략으로 등록하고 등록 이후 새 거래일만 누적합니다.

- 누락 거래일 자동 재생
- 인증/인증해제는 검증 기준일의 **다음 거래일부터** 효력
- 전략/파라미터가 정확히 일치할 때만 `FROZEN_VERIFIED`
- 과거 결과를 다시 최적화하지 않음

## ④ 최종 전진증거 게이트
다음 조건을 모두 만족하기 전에는 `전진검증완료`가 되지 않습니다.

- `FROZEN_VERIFIED`
- 최소 60거래일
- 최소 5회 완료거래
- 전진 누적수익 > 0
- 전진 MDD -10% 이내
- 승률 40% 이상
- PF 1.10 이상
- 추가 비용 스트레스 후 수익 > 0
- 거래수익 bootstrap 양수확률 70% 이상
- sign-test 및 추적후보 전체 BH 다중검정

30거래일 이후 전진수익 -10% 이하 또는 MDD -15% 이하이면 `전진실패`로 표시하지만 기록은 삭제하지 않습니다.

## ⑤ 포트폴리오 중복위험
- 최근 1년 일간수익률 상관관계
- 공통 120거래일 이상 요구
- 상관 0.80 이상은 동일 위험군으로 군집
- 같은 군집에서 여러 종목이 최종통과해도 증거가 가장 강한 1종목만 대표 허용

## ⑥ RAW 체결가 모의자동매매
검증 엔진의 연구용 가격과 가상계좌의 체결가격을 분리합니다.

### 가격 기준
- 연구/백테스트: `ADJUSTED_RESEARCH`
- 가상 주문/체결/계좌평가: `RAW_EXECUTION`
- 배당이나 분할 때문에 미래에 과거 조정주가가 바뀌어도 이미 기록된 가상 체결가를 다시 쓰지 않음

### 계좌 규칙
- KR 시작자금: 10,000,000 KRW
- US 시작자금: 10,000 USD
- 종목당 최대 계좌자산 25%
- 현금 최소 10% 유지
- 시장별 최대 3종목
- 동일 상관군집 동시보유 1종목
- 공매도·레버리지 없음
- 편도 수수료 0.15% + 슬리피지 0.05%
- 계좌 고점 대비 최대낙폭 -10% 도달 시 신규매수 영구 중지, 기존 포지션 청산은 허용

### 기업행동
- 현금배당: 보유수량 기준 가상 현금/배당수익 반영(세금은 모델링하지 않음)
- 주식분할: 정수 수량으로 안전하게 환산되는 경우 수량/진입단가 조정
- fractional cash-in-lieu가 필요한 애매한 분할은 임의 계산하지 않고 fail-closed

### 트랜잭션 저장
`paper_broker_safe.py`가 한 사이클을 메모리에서 먼저 계산합니다. 가격·기업행동·계좌평가 ERROR가 하나라도 있으면 **그 실행의 계좌 변경을 전부 폐기**하고 이전 정상 상태를 보존합니다.

`broker_health.py`가 매 실행 후 다음을 검사합니다.
- `RAW_EXECUTION` 가격기준
- raw broker 버전
- 음수 현금/비정상 수량·가격·원가
- 시장별 보유한도
- 동일 상관군집 중복보유
- -10% DD risk halt
- 기업행동 ledger 중복
- 중복 FILLED 주문키

## 자동 실행
GitHub Actions:

1. 평일 FULL80 파이프라인
`80종목 → 동결 2차 → 전진모의 → 최종게이트 → 상관게이트 → RAW 모의브로커 → health`

2. 한국장 마감 후 lightweight paper cycle
`전진모의 → 최종게이트 → 상관게이트 → RAW 모의브로커 → health`

두 작업은 같은 concurrency group을 사용해 계좌 상태를 동시에 수정하지 않습니다.

## 주요 파일
- `engine.py` — 전략/AI/누수방지 백테스트 엔진
- `market_data.py` — adjusted research / raw execution 데이터 분리와 무결성 검사
- `tools/autonomous_scan.py` — FULL80 및 fail-closed 1차검증
- `tools/stress_confirm.py` — purged 동결 2차검증
- `tools/paper_forward.py` — forward-only 모의추적
- `tools/promotion_gate.py` — 전진증거 게이트
- `tools/portfolio_gate.py` — 상관/군집대표 게이트
- `tools/paper_broker_raw.py` — raw 체결 및 기업행동 회계
- `tools/paper_broker_safe.py` — 트랜잭션형 fail-closed 저장
- `tools/broker_health.py` — 계좌 회계·리스크 invariant 검사
- `streamlit_app.py` — v9.1 웹 대시보드
- `tests/` — 누수, embargo, 데이터, 체결, 기업행동, 계좌, 통계 테스트

## 핵심 원칙
기준을 낮춰 억지로 후보를 만들지 않습니다. 후보가 없으면 `관망`이 정상입니다. `전진검증완료`, `포트폴리오허용`, shadow `BUY` 역시 실제 매수 지시가 아닙니다.
