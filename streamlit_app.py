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
TRACKER_VERSION = "paper-forward-1.2-frozen-admission"
GATE_VERSION = "promotion-gate-1.3-frozen-admission"
PORTFOLIO_VERSION = "portfolio-gate-1.1-cluster-leader"
BROKER_VERSION = "paper-broker-1.2-verification-exit"
HEALTH_VERSION = "broker-health-1.0"

st.set_page_config(page_title="APEX Autonomous Validation v8.9", page_icon="🧠", layout="wide")
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
      .block-container{padding:1rem .8rem 2rem;max-width:1280px}
      h1{font-size:clamp(1.45rem,6vw,2.25rem)!important}
      .stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
      [data-testid="stMetricValue"]{font-size:clamp(1.05rem,5vw,1.7rem)}
      @media(max-width:768px){[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}}
    </style>
    """,
    unsafe_allow_html=True,
)


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


def bh_qvalues(values):
    p = np.asarray(values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    raw = ranked * len(ranked) / np.arange(1, len(ranked) + 1)
    adj = np.minimum.accumulate(raw[::-1])[::-1]
    out = np.empty(len(ranked))
    out[order] = np.clip(adj, 0, 1)
    q[np.where(valid)[0]] = out
    return q


def manual_control(df):
    out = df.copy()
    out["다중검정q"] = bh_qvalues(out["타이밍p"].to_numpy())
    grades, passes = [], []
    for _, row in out.iterrows():
        grade, q = row["등급"], row["다중검정q"]
        if grade == "A" and np.isfinite(q) and q <= 0.20:
            final, ok = "A", True
        elif grade in {"A", "B"}:
            final, ok = "B", False
        elif grade == "관찰":
            final, ok = "관찰", False
        else:
            final, ok = "탈락", False
        grades.append(final)
        passes.append("✅" if ok else "❌")
    out["최종등급"] = grades
    out["최종통과"] = passes
    return out


def format_columns(df, percent_cols=(), number_cols=()):
    show = df.copy()
    for c in percent_cols:
        if c in show:
            show[c] = pd.to_numeric(show[c], errors="coerce").apply(pct)
    for c in number_cols:
        if c in show:
            show[c] = pd.to_numeric(show[c], errors="coerce").apply(num)
    return show


def render_primary():
    df = safe_csv("reports/latest_validation.csv")
    with st.expander("① 📡 80종목 전체 자동 스캔 · 전략 동결", expanded=True):
        if df.empty:
            st.info("자동 스캔 결과를 기다리는 중입니다.")
            return
        version = str(df.get("엔진버전", pd.Series(["legacy"])).iloc[0])
        if version != PRIMARY_VERSION:
            st.warning(f"이전 결과 {version} · {PRIMARY_VERSION} 대기 중")
            return
        watch = df[df["최종등급"].isin(["A", "B", "관찰"])]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("전체 대상", "80개")
        c2.metric("분석", f"{len(df)}개")
        c3.metric("A 통과", f"{(df['최종통과'] == '✅').sum()}개")
        c4.metric("2차 대상", f"{len(watch)}개")
        st.caption(f"{version} · 전략/파라미터/기준일 동결 · 조정 OHLCV 무결성 검사")
        show = format_columns(df, ["TEST수익", "MDD"], ["PF", "샤프", "타이밍p", "다중검정q"])
        cols = [c for c in ["최종등급", "시장", "종목", "선택전략", "전략파라미터", "데이터기준일", "TEST수익", "MDD", "TEST거래수", "PF", "샤프", "타이밍p", "다중검정q", "탈락사유"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_confirmation():
    df = safe_csv("reports/latest_confirmation.csv")
    with st.expander("② 🧪 동일 파라미터 2차 재현·스트레스", expanded=True):
        if df.empty:
            st.info("2차 결과를 기다리는 중입니다.")
            return
        version = str(df.get("확인엔진", pd.Series(["legacy"])).iloc[0])
        if version != CONFIRM_VERSION:
            st.warning(f"이전 결과 {version} · {CONFIRM_VERSION} 대기 중")
            return
        confirmed = df[df["2차통과"] == "✅"]
        c1, c2, c3 = st.columns(3)
        c1.metric("2차 검사", f"{len(df)}개")
        c2.metric("확인후보", f"{len(confirmed)}개")
        c3.metric("엔진", version)
        show = format_columns(df, ["1차TEST수익", "재현TEST수익", "재현오차", "비용중앙수익", "파라미터양수비율", "10년양수비율", "10년중앙수익"])
        cols = [c for c in ["2차통과", "2차등급", "종목", "전략", "전략파라미터", "1차데이터기준일", "1차TEST수익", "재현TEST수익", "재현오차", "비용중앙수익", "파라미터양수비율", "10년양수비율", "10년중앙수익", "10년거래수", "보류사유"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_forward():
    df = safe_csv("reports/paper_forward.csv")
    with st.expander("③ 🧾 동결재검증 전진 모의", expanded=True):
        if df.empty:
            st.info("전진 모의 후보가 아직 없습니다.")
            return
        if "시각UTC" in df:
            df = df.sort_values("시각UTC")
        latest = df.drop_duplicates("코드", keep="last")
        c1, c2, c3 = st.columns(3)
        c1.metric("추적", f"{len(latest)}개")
        trades = int(pd.to_numeric(latest.get("완료거래", pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
        c2.metric("완료거래", f"{trades}회")
        c3.metric("최고 전진수익", pct(pd.to_numeric(latest.get("전진누적수익", pd.Series(dtype=float)), errors="coerce").max()))
        tracker = str(latest.get("트래커", pd.Series([TRACKER_VERSION])).iloc[-1])
        st.caption(f"{tracker} · 누락 거래일 자동 재생 · 파라미터 고정")
        show = format_columns(latest, ["승률", "전진누적수익", "전진MDD"], ["PF"])
        cols = [c for c in ["동결검증", "종목", "전략", "신호기준일", "종가신호", "현재포지션", "관측거래일", "완료거래", "승률", "PF", "전진누적수익", "전진MDD", "업데이트", "오류"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_promotion():
    df = safe_csv("reports/promotion_status.csv")
    with st.expander("④ 🛡️ 최종 전진증거 게이트", expanded=True):
        if df.empty:
            st.info("최종 게이트 결과를 기다리는 중입니다.")
            return
        gate = str(df.get("게이트", pd.Series(["legacy"])).iloc[0])
        if gate != GATE_VERSION:
            st.warning(f"이전 게이트 {gate} · {GATE_VERSION} 대기 중")
            return
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("추적", f"{len(df)}개")
        c2.metric("검증완료", f"{(df['최종상태'] == '전진검증완료').sum()}개")
        c3.metric("관찰중", f"{(df['최종상태'] == '관찰중').sum()}개")
        c4.metric("전진실패", f"{(df['최종상태'] == '전진실패').sum()}개")
        st.caption(f"{gate} · 60거래일·5완료거래 + 비용/부트스트랩/sign-test/BH")
        show = format_columns(df, ["전진누적수익", "전진MDD", "승률", "비용스트레스수익", "부트스트랩양수확률"], ["PF", "방향성p", "전진다중검정q"])
        cols = [c for c in ["승격가능", "최종상태", "동결검증", "종목", "전략", "관측거래일", "완료거래", "전진누적수익", "전진MDD", "승률", "PF", "비용스트레스수익", "부트스트랩양수확률", "방향성p", "전진다중검정q", "현재포지션", "대기조건"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_portfolio():
    df = safe_csv("reports/portfolio_risk.csv")
    with st.expander("⑤ 🧩 포트폴리오 중복위험·군집대표 게이트", expanded=True):
        if df.empty:
            st.info("포트폴리오 결과를 기다리는 중입니다.")
            return
        version = str(df.get("게이트", pd.Series(["legacy"])).iloc[0])
        if version != PORTFOLIO_VERSION:
            st.warning(f"이전 결과 {version} · {PORTFOLIO_VERSION} 대기 중")
            return
        corr = pd.to_numeric(df.get("최대상관", pd.Series(dtype=float)), errors="coerce")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("추적", f"{len(df)}개")
        c2.metric("고상관 경고", f"{(df.get('중복위험', pd.Series(dtype=str)) == '⚠️').sum()}개")
        c3.metric("포트폴리오 허용", f"{(df.get('포트폴리오허용', pd.Series(dtype=str)) == '✅').sum()}개")
        c4.metric("최대 상관", "-" if corr.dropna().empty else f"{corr.max():.3f}")
        st.caption(f"{version} · 상관 0.80 이상은 동일 위험군 · 최종통과 시 군집당 1개 대표")
        show = format_columns(df, number_cols=["최대상관"])
        cols = [c for c in ["포트폴리오허용", "최종상태", "동결검증", "종목", "시장", "전략", "상관군집", "군집대표", "군집대표종목", "최대상관", "최대상관대상", "공통거래일", "중복위험", "포트폴리오대기조건", "데이터오류"] if c in show]
        st.dataframe(show[cols], use_container_width=True, hide_index=True)


def render_broker():
    state = safe_json("reports/paper_broker_state.json")
    health = safe_json("reports/paper_broker_health.json")
    account_log = safe_csv("reports/paper_account.csv")
    positions = safe_csv("reports/paper_positions.csv")
    orders = safe_csv("reports/paper_orders.csv")
    with st.expander("⑥ 🤖 위험제어 모의자동매매 가상계좌", expanded=True):
        if not state:
            st.info("모의자동매매 계좌 초기화를 기다리는 중입니다.")
            return
        version = str(state.get("version", "legacy"))
        if version != BROKER_VERSION:
            st.warning(f"브로커 상태 {version} · 새 {BROKER_VERSION} 결과 대기 중")
        if health:
            if bool(health.get("ok")):
                st.success(f"✅ 브로커 회계·리스크 무결성 정상 · {health.get('version', HEALTH_VERSION)}")
            else:
                st.error("⛔ 브로커 health 오류 · 새 모의매매 결과를 신뢰하지 않습니다: " + ", ".join(map(str, health.get("errors", []))))
        else:
            st.warning("브로커 health 결과 생성 대기 중")

        accounts = state.get("accounts", {})
        kr, us = accounts.get("KR", {}), accounts.get("US", {})

        def equity(a):
            return float(a.get("last_equity", a.get("cash", 0.0))) if a else np.nan

        def account_return(a):
            initial = float(a.get("initial_cash", 0.0)) if a else 0.0
            return equity(a) / initial - 1 if initial > 0 else np.nan

        filled = orders[orders["상태"].astype(str) == "FILLED"] if not orders.empty and "상태" in orders else pd.DataFrame()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("KR 가상자산", money(equity(kr), kr.get("currency", "KRW")), pct(account_return(kr)))
        c2.metric("US 가상자산", money(equity(us), us.get("currency", "USD")), pct(account_return(us)))
        c3.metric("현재 보유", f"{len(positions)}종목")
        c4.metric("누적 체결", f"{len(filled)}건")

        halted = [market for market, account in accounts.items() if bool(account.get("risk_halt"))]
        if halted:
            st.error("⛔ 신규매수 중지: " + ", ".join(halted) + " · 보유 청산만 허용")
        else:
            st.info("위험중지 없음 · 현재 설정 범위 내에서만 신규 모의매수 가능")
        st.caption(
            f"{version} · 실계좌 주문 NEVER · 종목당 최대 25% · 현금 10% 유지 · 시장별 최대 3종목 · "
            "동일 상관군집 1종목 · 편도 비용 0.15% + 슬리피지 0.05% · 고점대비 -10%면 신규매수 영구 중지 · "
            "동결검증 취소 시 다음 시가 강제청산"
        )
        st.warning("⑥의 가상 손익은 ①~⑤의 후보 검증이나 승격에 절대 사용하지 않습니다.")

        state_rows = []
        for market, account in accounts.items():
            eq = equity(account)
            peak = float(account.get("peak_equity", eq))
            state_rows.append({
                "시장": market,
                "통화": account.get("currency"),
                "현금": float(account.get("cash", 0.0)),
                "총자산": eq,
                "누적수익률": account_return(account),
                "현재낙폭": eq / peak - 1 if peak > 0 else 0.0,
                "최대낙폭": float(account.get("max_drawdown", 0.0)),
                "신규매수중지": "⛔" if account.get("risk_halt") else "-",
                "보유종목수": len(account.get("positions", {})),
                "완료거래": int(account.get("completed_trades", 0)),
                "실현손익": float(account.get("realized_pnl", 0.0)),
            })
        show_accounts = format_columns(pd.DataFrame(state_rows), ["누적수익률", "현재낙폭", "최대낙폭"])
        st.dataframe(show_accounts, use_container_width=True, hide_index=True)

        st.markdown("**현재 모의 보유종목**")
        if positions.empty:
            st.info("현재 보유 없음 · CASH")
        else:
            cols = [c for c in ["시장", "통화", "코드", "상관군집", "수량", "진입일", "평균진입가", "최근가격", "평가금액", "미실현손익"] if c in positions]
            st.dataframe(positions[cols], use_container_width=True, hide_index=True)

        st.markdown("**최근 모의 주문**")
        if orders.empty:
            st.info("아직 자동 체결 주문이 없습니다.")
        else:
            recent = orders.tail(20)
            cols = [c for c in ["체결일", "시장", "코드", "구분", "상태", "사유", "상관군집", "수량", "체결가", "수수료", "실현손익"] if c in recent]
            st.dataframe(recent[cols], use_container_width=True, hide_index=True)

        if not account_log.empty:
            with st.expander("가상계좌 기록 보기"):
                hist = format_columns(account_log.tail(30), ["누적수익률", "현재낙폭", "최대낙폭"])
                st.dataframe(hist, use_container_width=True, hide_index=True)


st.title("🧠 APEX Autonomous Validation v8.9")
st.caption("80종목 전체검정 → 동결 2차 → 전진검증 → 통계게이트 → 상관위험 → health-gated 모의자동매매")
st.warning("연구·모의투자용입니다. 미래 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")
checks = run_self_tests()
if not checks or not all(checks.values()):
    st.error(f"엔진 자가검증 실패: {checks}")
    st.stop()
st.success(f"엔진 자가검증 통과 · {sum(checks.values())}/{len(checks)}")

render_primary()
render_confirmation()
render_forward()
render_promotion()
render_portfolio()
render_broker()

with st.sidebar:
    st.header("수동 검증")
    market_choice = st.selectbox("시장", ["한국 40종목", "미국 40종목", "직접 입력"])
    period = st.selectbox("기간", ["5y", "10y"], index=0)
    max_count = st.slider("검사 종목", 4, 30, 12, 2)
    fast_mode = st.toggle("무료 서버 빠른 모드", value=True)
    future = st.slider("AI 예측 거래일", 2, 10, 5)
    target_pct = st.slider("AI 상승 기준(%)", 0.0, 5.0, 1.0, .1) / 100
    fee = st.slider("편도 비용(%)", 0.05, 0.30, 0.15, .01) / 100
    custom = st.text_area("직접 종목코드", "005930.KS,000660.KS,NVDA,AAPL")
    run = st.button("🚀 수동 검증", type="primary")

if not run:
    st.info("자동 파이프라인은 평일마다 ①→⑥을 갱신하고, 한국장 마감 후에는 가벼운 모의매매 사이클을 한 번 더 실행합니다.")
    st.stop()

if market_choice == "한국 40종목":
    universe, benchmark = list(KOREA.items())[:max_count], "^KS11"
elif market_choice == "미국 40종목":
    universe, benchmark = list(USA.items())[:max_count], "SPY"
else:
    codes = [x.strip().upper() for x in custom.split(",") if x.strip()][:max_count]
    universe = [(x, x) for x in codes]
    benchmark = "^KS11" if any(x.endswith((".KS", ".KQ")) for x in codes) else "SPY"

progress = st.progress(0, text="데이터 품질검사 포함 검증 준비 중...")
rows, errors = [], []
try:
    market = download_ohlcv(benchmark, period=period)
    for i, (name, ticker) in enumerate(universe):
        progress.progress(i / max(1, len(universe)), text=f"{i+1}/{len(universe)} {name}")
        try:
            raw = download_ohlcv(ticker, period=period)
            data = make_features(raw, market, future, target_pct)
            rows.append(analyze_frame(name, ticker, data, future, fee, fast_mode))
        except Exception as e:
            errors.append(f"{name}: {e}")
    progress.progress(1.0, text="검증 완료")
except Exception as e:
    st.error(f"시장 데이터 오류: {e}")
    st.stop()

if not rows:
    st.error("분석 가능한 종목이 없습니다.")
    if errors:
        st.code("\n".join(errors))
    st.stop()

result = manual_control(pd.DataFrame(rows)).sort_values("점수", ascending=False).reset_index(drop=True)
c1, c2, c3 = st.columns(3)
c1.metric("검사", f"{len(result)}개")
c2.metric("A 통과", f"{(result['최종통과'] == '✅').sum()}개")
c3.metric("최고 TEST", pct(result["TEST수익"].max()))
show = format_columns(result, ["TEST수익", "최근63일", "MDD", "승률"], ["PF", "샤프", "타이밍p", "다중검정q", "점수"])
cols = [c for c in ["최종통과", "최종등급", "종목", "코드", "선택전략", "TEST수익", "최근63일", "MDD", "TEST거래수", "승률", "PF", "샤프", "타이밍p", "다중검정q", "탈락사유", "점수"] if c in show]
st.dataframe(show[cols], use_container_width=True, hide_index=True)
st.download_button("검증 결과 CSV", result.to_csv(index=False).encode("utf-8-sig"), "apex_v89_manual_validation.csv", "text/csv")
if errors:
    with st.expander(f"분석 제외 {len(errors)}개"):
        st.code("\n".join(errors))
