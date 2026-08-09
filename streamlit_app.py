import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from engine import analyze_frame, make_features, run_self_tests
from market_data import download_ohlcv
from tools.autonomous_scan import KOREA, USA

warnings.filterwarnings("ignore")

PRIMARY_VERSION = "8.5-frozen-primary"
CONFIRM_VERSION = "8.5-frozen-confirm"
TRACKER_VERSION = "paper-forward-1.3-verification-timing"
GATE_VERSION = "promotion-gate-1.3-frozen-admission"
PORTFOLIO_VERSION = "portfolio-gate-1.1-cluster-leader"
BROKER_VERSION = "paper-broker-1.4-raw-execution"
HEALTH_VERSION = "broker-health-1.1-raw-execution"
PRICE_BASIS = "RAW_EXECUTION"

st.set_page_config(page_title="APEX Autonomous Validation v9.1", page_icon="🧠", layout="wide")
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
      .block-container{padding:1rem .8rem 2rem;max-width:1280px}
      h1{font-size:clamp(1.45rem,6vw,2.25rem)!important}
      .stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
      [data-testid="stMetricValue"]{font-size:clamp(1.0rem,5vw,1.65rem)}
      @media(max-width:768px){[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}}
    </style>
    """,
    unsafe_allow_html=True,
)


def safe_csv(path):
    try:
        p = Path(path)
        return pd.read_csv(p) if p.exists() and p.stat().st_size else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def safe_json(path):
    try:
        p = Path(path)
        if not p.exists() or not p.stat().st_size:
            return {}
        obj = json.loads(p.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def pct(x):
    try:
        v = float(x)
        return "-" if not np.isfinite(v) else f"{v*100:.2f}%"
    except Exception:
        return "-"


def num(x, digits=3):
    try:
        v = float(x)
        return "-" if not np.isfinite(v) else f"{v:.{digits}f}"
    except Exception:
        return "-"


def money(x, currency):
    try:
        v = float(x)
        if not np.isfinite(v):
            return "-"
        return f"₩{v:,.0f}" if str(currency) == "KRW" else f"${v:,.2f}"
    except Exception:
        return "-"


def fmt(df, pct_cols=(), num_cols=()):
    out = df.copy()
    for c in pct_cols:
        if c in out:
            out[c] = pd.to_numeric(out[c], errors="coerce").apply(pct)
    for c in num_cols:
        if c in out:
            out[c] = pd.to_numeric(out[c], errors="coerce").apply(num)
    return out


def bh_qvalues(values):
    p = np.asarray(values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    raw = ranked * max(80, len(ranked)) / np.arange(1, len(ranked) + 1)
    adj = np.minimum.accumulate(raw[::-1])[::-1]
    tmp = np.empty(len(ranked))
    tmp[order] = np.clip(adj, 0, 1)
    q[np.where(valid)[0]] = tmp
    return q


def render_primary():
    df = safe_csv("reports/latest_validation.csv")
    errors = safe_json("reports/latest_errors.json")
    failed = safe_json("reports/failed_scan_errors.json")
    with st.expander("① 📡 FULL80 · purge/embargo 자동검증", expanded=True):
        if failed:
            st.error("⛔ 최근 FULL80 실행은 fail-closed 처리됨 · 이전 정상 결과 유지")
        if df.empty:
            st.info("자동 스캔 결과 대기 중")
            return
        version = str(df.get("엔진버전", pd.Series(["legacy"])).iloc[0])
        watch = df[df.get("최종등급", pd.Series(index=df.index, dtype=str)).isin(["A", "B", "관찰"])]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("전체 대상", "80개")
        c2.metric("결과행", f"{len(df)}개")
        c3.metric("진짜 오류", f"{len(errors) if isinstance(errors, list) else 0}개")
        c4.metric("A 통과", f"{int((df.get('최종통과', pd.Series(dtype=str)) == '✅').sum())}개")
        embargo = int(pd.to_numeric(df.get("Embargo거래일", pd.Series([5])), errors="coerce").dropna().iloc[0]) if "Embargo거래일" in df else 5
        st.caption(f"{version} · 75% 경계 앞 {embargo}거래일 purge/embargo · 2차 대상 {len(watch)}개 · 오류 발생 시 정상 리포트 보존")
        if version != PRIMARY_VERSION:
            st.warning(f"현재 보고서 엔진 {version} · 기대 {PRIMARY_VERSION}")
        show = fmt(df, ["TEST수익", "MDD", "OHLC최대보정폭"], ["PF", "샤프", "타이밍p", "다중검정q"])
        cols = [c for c in ["최종등급", "시장", "종목", "선택전략", "전략파라미터", "학습끝일", "TEST시작일", "Embargo거래일", "데이터기준일", "OHLC보정봉수", "TEST수익", "MDD", "TEST거래수", "PF", "샤프", "타이밍p", "다중검정q", "탈락사유"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_confirmation():
    df = safe_csv("reports/latest_confirmation.csv")
    failed = safe_json("reports/failed_confirmation_errors.json")
    with st.expander("② 🧪 동일 파라미터 · 동일 embargo 2차 스트레스", expanded=True):
        if failed:
            st.error("⛔ 최근 2차 검증은 fail-closed 처리됨 · 이전 정상 확인결과 유지")
        if df.empty:
            st.info("2차 결과 대기 중")
            return
        version = str(df.get("확인엔진", pd.Series(["legacy"])).iloc[0])
        confirmed = df[df.get("2차통과", pd.Series(index=df.index, dtype=str)) == "✅"]
        c1, c2, c3 = st.columns(3)
        c1.metric("검사", f"{len(df)}개")
        c2.metric("확인후보", f"{len(confirmed)}개")
        c3.metric("엔진", version)
        if version != CONFIRM_VERSION:
            st.warning(f"현재 2차 엔진 {version} · 기대 {CONFIRM_VERSION}")
        show = fmt(df, ["1차TEST수익", "재현TEST수익", "재현오차", "비용중앙수익", "파라미터양수비율", "10년양수비율", "10년중앙수익"])
        cols = [c for c in ["2차통과", "2차등급", "종목", "전략", "전략파라미터", "재현학습끝일", "재현TEST시작일", "재현Embargo거래일", "재현오차", "비용중앙수익", "파라미터양수비율", "10년양수비율", "10년중앙수익", "10년거래수", "보류사유"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_forward():
    df = safe_csv("reports/paper_forward.csv")
    with st.expander("③ 🧾 전진 모의검증", expanded=True):
        if df.empty:
            st.info("전진 모의 후보 없음")
            return
        if "시각UTC" in df:
            df = df.sort_values("시각UTC")
        latest = df.drop_duplicates("코드", keep="last")
        tracker = str(latest.get("트래커", pd.Series(["legacy"])).iloc[-1])
        c1, c2, c3 = st.columns(3)
        c1.metric("추적", f"{len(latest)}개")
        c2.metric("완료거래", f"{int(pd.to_numeric(latest.get('완료거래'), errors='coerce').fillna(0).sum())}회")
        c3.metric("최고 전진수익", pct(pd.to_numeric(latest.get("전진누적수익"), errors="coerce").max()))
        st.caption(f"{tracker} · 인증/해제는 기준일 다음 거래일부터 효력 · 누락 거래일 순차 재생")
        if tracker != TRACKER_VERSION:
            st.warning(f"현재 tracker {tracker} · 기대 {TRACKER_VERSION}")
        show = fmt(latest, ["승률", "전진누적수익", "전진MDD"], ["PF"])
        cols = [c for c in ["동결검증", "종목", "전략", "신호기준일", "종가신호", "현재포지션", "관측거래일", "완료거래", "승률", "PF", "전진누적수익", "전진MDD", "업데이트", "오류"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_gate():
    df = safe_csv("reports/promotion_status.csv")
    with st.expander("④ 🛡️ 최종 전진증거 게이트", expanded=True):
        if df.empty:
            st.info("게이트 결과 대기 중")
            return
        gate = str(df.get("게이트", pd.Series(["legacy"])).iloc[0])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("추적", f"{len(df)}개")
        c2.metric("검증완료", f"{int((df.get('최종상태') == '전진검증완료').sum())}개")
        c3.metric("관찰중", f"{int((df.get('최종상태') == '관찰중').sum())}개")
        c4.metric("실패", f"{int((df.get('최종상태') == '전진실패').sum())}개")
        st.caption(f"{gate} · 60거래일·5완료거래·수익/MDD/PF·비용·부트스트랩·다중검정")
        show = fmt(df, ["전진누적수익", "전진MDD", "승률", "비용스트레스수익", "부트스트랩양수확률"], ["PF", "방향성p", "전진다중검정q"])
        cols = [c for c in ["승격가능", "최종상태", "동결검증", "종목", "전략", "관측거래일", "완료거래", "전진누적수익", "전진MDD", "승률", "PF", "비용스트레스수익", "부트스트랩양수확률", "전진다중검정q", "현재포지션", "대기조건"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_portfolio():
    df = safe_csv("reports/portfolio_risk.csv")
    with st.expander("⑤ 🧩 포트폴리오 중복위험", expanded=True):
        if df.empty:
            st.info("포트폴리오 결과 대기 중")
            return
        corr = pd.to_numeric(df.get("최대상관", pd.Series(dtype=float)), errors="coerce")
        c1, c2, c3 = st.columns(3)
        c1.metric("추적", f"{len(df)}개")
        c2.metric("고상관 경고", f"{int((df.get('중복위험') == '⚠️').sum())}개")
        c3.metric("최대상관", "-" if corr.dropna().empty else f"{corr.max():.3f}")
        st.caption("상관 0.80 이상 동일 위험군 · 최종통과 시 군집당 대표 1종목")
        show = fmt(df, num_cols=["최대상관"])
        cols = [c for c in ["포트폴리오허용", "최종상태", "종목", "시장", "전략", "상관군집", "군집대표", "군집대표종목", "최대상관", "최대상관대상", "중복위험", "포트폴리오대기조건"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_broker():
    state = safe_json("reports/paper_broker_state.json")
    health = safe_json("reports/paper_broker_health.json")
    failed = safe_json("reports/failed_paper_broker.json")
    positions = safe_csv("reports/paper_positions.csv")
    orders = safe_csv("reports/paper_orders.csv")
    account_log = safe_csv("reports/paper_account.csv")
    with st.expander("⑥ 🤖 RAW 체결가 모의자동매매", expanded=True):
        if failed:
            st.error("⛔ 최근 모의브로커 실행 실패 · 이전 정상 계좌 상태 보존")
        if not state:
            st.info("모의계좌 초기화 대기 중")
            return
        version = str(state.get("version", "legacy"))
        basis = str(state.get("price_basis", "legacy"))
        if health.get("ok") is True and health.get("version") == HEALTH_VERSION:
            st.success(f"✅ 회계·리스크 health 정상 · {HEALTH_VERSION}")
        elif health:
            st.error("⛔ health 오류: " + ", ".join(map(str, health.get("errors", []))))
        else:
            st.warning("health 결과 대기 중")
        if version != BROKER_VERSION or basis != PRICE_BASIS:
            st.warning(f"현재 {version} / {basis} · 기대 {BROKER_VERSION} / {PRICE_BASIS}")

        accounts = state.get("accounts", {})
        kr, us = accounts.get("KR", {}), accounts.get("US", {})
        def equity(a): return float(a.get("last_equity", a.get("cash", 0.0))) if a else np.nan
        def ret(a):
            initial = float(a.get("initial_cash", 0.0)) if a else 0.0
            return equity(a) / initial - 1 if initial > 0 else np.nan
        trade_fills = orders[(orders["상태"].astype(str) == "FILLED") & orders.get("구분", pd.Series(index=orders.index, dtype=str)).isin(["BUY", "SELL"])] if not orders.empty and "상태" in orders else pd.DataFrame()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("KR 가상자산", money(equity(kr), "KRW"), pct(ret(kr)))
        c2.metric("US 가상자산", money(equity(us), "USD"), pct(ret(us)))
        c3.metric("보유", f"{len(positions)}종목")
        c4.metric("매매체결", f"{len(trade_fills)}건")
        halted = [m for m, a in accounts.items() if bool(a.get("risk_halt"))]
        st.error("⛔ 신규매수 중지: " + ", ".join(halted) + " · 청산만 허용") if halted else st.info("신규매수 위험중지 없음")
        st.caption(
            f"{version} · {basis} · 실계좌 주문 NEVER · 종목당 25% · 현금 10% · 시장별 3종목 · "
            "동일상관군 1종목 · 편도 수수료 0.15% + 슬리피지 0.05% · -10% DD 신규매수 중지 · "
            "배당 현금반영 · 정수형 분할 수량조정 · 오류 시 트랜잭션 전체 폐기"
        )

        rows = []
        for market, a in accounts.items():
            eq = equity(a); peak = float(a.get("peak_equity", eq)); initial = float(a.get("initial_cash", eq))
            rows.append({
                "시장": market, "통화": a.get("currency"), "현금": float(a.get("cash", 0.0)), "총자산": eq,
                "누적수익률": eq / initial - 1 if initial > 0 else np.nan,
                "현재낙폭": eq / peak - 1 if peak > 0 else 0.0, "최대낙폭": float(a.get("max_drawdown", 0.0)),
                "배당수익": float(a.get("dividend_income", 0.0)), "신규매수중지": "⛔" if a.get("risk_halt") else "-",
                "보유종목수": len(a.get("positions", {})), "완료거래": int(a.get("completed_trades", 0)),
                "실현손익": float(a.get("realized_pnl", 0.0)),
            })
        st.dataframe(fmt(pd.DataFrame(rows), ["누적수익률", "현재낙폭", "최대낙폭"]), use_container_width=True, hide_index=True)
        st.markdown("**현재 보유**")
        st.info("CASH") if positions.empty else st.dataframe(positions, use_container_width=True, hide_index=True)
        st.markdown("**최근 주문·기업행동**")
        st.info("아직 이벤트 없음") if orders.empty else st.dataframe(orders.tail(25), use_container_width=True, hide_index=True)
        if not account_log.empty:
            with st.expander("계좌 기록"):
                st.dataframe(fmt(account_log.tail(30), ["누적수익률", "현재낙폭", "최대낙폭"]), use_container_width=True, hide_index=True)


st.title("🧠 APEX Autonomous Validation v9.1")
st.caption("FULL80 → 5-bar purge/embargo → 동결 2차 → 전진검증 → 통계게이트 → 상관위험 → RAW 체결가 모의자동매매")
st.warning("연구·모의투자용입니다. 실제 주문을 전송하지 않으며 미래 수익을 보장하지 않습니다.")
checks = run_self_tests()
if not checks or not all(checks.values()):
    st.error(f"엔진 자가검증 실패: {checks}")
    st.stop()
st.success(f"엔진 자가검증 통과 · {sum(checks.values())}/{len(checks)}")

render_primary(); render_confirmation(); render_forward(); render_gate(); render_portfolio(); render_broker()

with st.sidebar:
    st.header("수동 검증")
    market_choice = st.selectbox("시장", ["한국 40종목", "미국 40종목", "직접 입력"])
    period = st.selectbox("기간", ["5y", "10y"], index=0)
    max_count = st.slider("검사 종목", 4, 40, 12, 2)
    fast_mode = st.toggle("무료 서버 빠른 모드", value=True)
    future = st.slider("AI 예측 거래일", 2, 10, 5)
    target_pct = st.slider("AI 상승 기준(%)", 0.0, 5.0, 1.0, .1) / 100
    fee = st.slider("편도 비용(%)", 0.05, 0.30, 0.15, .01) / 100
    custom = st.text_area("직접 종목코드", "005930.KS,000660.KS,NVDA,AAPL")
    run = st.button("🚀 수동 검증", type="primary")

if not run:
    st.info("자동 파이프라인은 평일 FULL80 검증과 한국장 마감 후 빠른 RAW 모의사이클을 자동 실행합니다.")
    st.stop()

if market_choice == "한국 40종목":
    universe, benchmark = list(KOREA.items())[:max_count], "^KS11"
elif market_choice == "미국 40종목":
    universe, benchmark = list(USA.items())[:max_count], "SPY"
else:
    codes = [x.strip().upper() for x in custom.split(",") if x.strip()][:max_count]
    universe = [(x, x) for x in codes]
    benchmark = "^KS11" if any(x.endswith((".KS", ".KQ")) for x in codes) else "SPY"

progress = st.progress(0, text="검증 준비 중...")
rows, errors = [], []
try:
    market = download_ohlcv(benchmark, period=period)
    for i, (name, ticker) in enumerate(universe):
        progress.progress(i / max(1, len(universe)), text=f"{i+1}/{len(universe)} {name}")
        try:
            raw = download_ohlcv(ticker, period=period)
            data = make_features(raw, market, future, target_pct)
            row = analyze_frame(name, ticker, data, future, fee, fast_mode)
            row["OHLC보정봉수"] = int(raw.attrs.get("ohlcv_repaired_bars", 0))
            rows.append(row)
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    progress.progress(1.0, text="검증 완료")
except Exception as exc:
    st.error(f"시장 데이터 오류: {exc}")
    st.stop()

if not rows:
    st.error("분석 가능한 종목이 없습니다.")
    if errors: st.code("\n".join(errors))
    st.stop()

result = pd.DataFrame(rows)
result["다중검정q"] = bh_qvalues(result["타이밍p"].to_numpy())
result["최종등급"] = ["A" if g == "A" and np.isfinite(q) and q <= .20 else ("B" if g in {"A", "B"} else g) for g, q in zip(result["등급"], result["다중검정q"])]
result["최종통과"] = np.where(result["최종등급"] == "A", "✅", "❌")
result = result.sort_values("점수", ascending=False).reset_index(drop=True)
c1, c2, c3 = st.columns(3)
c1.metric("검사", f"{len(result)}개"); c2.metric("A 통과", f"{int((result['최종통과'] == '✅').sum())}개"); c3.metric("오류", f"{len(errors)}개")
show = fmt(result, ["TEST수익", "최근63일", "MDD", "승률"], ["PF", "샤프", "타이밍p", "다중검정q", "점수"])
cols = [c for c in ["최종통과", "최종등급", "종목", "코드", "선택전략", "학습끝일", "TEST시작일", "Embargo거래일", "TEST수익", "MDD", "TEST거래수", "승률", "PF", "샤프", "타이밍p", "다중검정q", "탈락사유", "점수"] if c in show]
st.dataframe(show[cols], use_container_width=True, hide_index=True)
st.download_button("검증 결과 CSV", result.to_csv(index=False).encode("utf-8-sig"), "apex_v91_manual_validation.csv", "text/csv")
if errors:
    with st.expander(f"분석 제외 {len(errors)}개"):
        st.code("\n".join(errors))
