import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from engine import analyze_frame, make_features, run_self_tests

EXPECTED_ENGINE_VERSION = "8.2-next-open"

st.set_page_config(page_title="APEX Autonomous Validation v8.2", page_icon="🧠", layout="wide")
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
    .block-container{padding:1rem .8rem 2rem;max-width:1280px}
    h1{font-size:clamp(1.45rem,6vw,2.25rem)!important}
    .stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
    [data-testid="stMetricValue"]{font-size:clamp(1.05rem,5vw,1.7rem)}
    @media(max-width:768px){
      [data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}
      [data-testid="stSidebar"]{min-width:91vw;max-width:91vw}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

KOREA = {
    "삼성전자":"005930.KS","SK하이닉스":"000660.KS","현대차":"005380.KS","기아":"000270.KS",
    "NAVER":"035420.KS","카카오":"035720.KS","삼성바이오로직스":"207940.KS","셀트리온":"068270.KS",
    "LG에너지솔루션":"373220.KS","POSCO홀딩스":"005490.KS","한화에어로스페이스":"012450.KS","HD현대중공업":"329180.KS",
    "KB금융":"105560.KS","신한지주":"055550.KS","하나금융지주":"086790.KS","우리금융지주":"316140.KS",
    "삼성물산":"028260.KS","삼성SDI":"006400.KS","LG화학":"051910.KS","LG전자":"066570.KS",
    "SK이노베이션":"096770.KS","SK텔레콤":"017670.KS","KT":"030200.KS","한국전력":"015760.KS",
    "두산에너빌리티":"034020.KS","현대로템":"064350.KS","한화오션":"042660.KS","대한항공":"003490.KS",
    "아모레퍼시픽":"090430.KS","KT&G":"033780.KS","삼성전기":"009150.KS","LG이노텍":"011070.KS",
    "삼성중공업":"010140.KS","기업은행":"024110.KS","포스코퓨처엠":"003670.KS","에코프로비엠":"247540.KQ",
    "에코프로":"086520.KQ","알테오젠":"196170.KQ","HLB":"028300.KQ","리노공업":"058470.KQ"
}
USA = {
    "Apple":"AAPL","Microsoft":"MSFT","NVIDIA":"NVDA","Amazon":"AMZN","Meta":"META","Alphabet":"GOOGL",
    "Tesla":"TSLA","Broadcom":"AVGO","AMD":"AMD","Netflix":"NFLX","JPMorgan":"JPM","Eli Lilly":"LLY",
    "Berkshire":"BRK-B","Visa":"V","Mastercard":"MA","Walmart":"WMT","Costco":"COST","Oracle":"ORCL",
    "Salesforce":"CRM","Adobe":"ADBE","Palantir":"PLTR","Micron":"MU","Qualcomm":"QCOM","Intel":"INTC",
    "Cisco":"CSCO","IBM":"IBM","Coca-Cola":"KO","PepsiCo":"PEP","McDonalds":"MCD","Nike":"NKE",
    "ExxonMobil":"XOM","Chevron":"CVX","UnitedHealth":"UNH","Johnson&Johnson":"JNJ","Merck":"MRK","AbbVie":"ABBV",
    "HomeDepot":"HD","Boeing":"BA","Caterpillar":"CAT","GoldmanSachs":"GS"
}

@st.cache_data(ttl=3600, show_spinner=False)
def download_one(ticker, period="5y"):
    d = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False, threads=False)
    if d is None or d.empty:
        raise ValueError("데이터 없음")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    need = ["Open","High","Low","Close","Volume"]
    if any(c not in d.columns for c in need):
        raise ValueError("OHLCV 오류")
    return d[need].dropna()


def pct(x):
    return "-" if x is None or not np.isfinite(x) else f"{x*100:.2f}%"


def bh_qvalues(values):
    p = np.asarray(values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any():
        return q
    pv = p[valid]
    order = np.argsort(pv)
    ranked = pv[order]
    m = len(ranked)
    raw = ranked * m / np.arange(1, m + 1)
    adj = np.minimum.accumulate(raw[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.clip(adj, 0, 1)
    q[np.where(valid)[0]] = out
    return q


def apply_portfolio_control(result):
    result = result.copy()
    result["다중검정q"] = bh_qvalues(result["타이밍p"].to_numpy())
    final_grade = []
    final_pass = []
    for _, row in result.iterrows():
        grade = row["등급"]
        q = row["다중검정q"]
        if grade == "A" and np.isfinite(q) and q <= 0.20:
            g, ok = "A", True
        elif grade == "A":
            g, ok = "B", False
        elif grade == "B":
            g, ok = "B", False
        elif grade == "관찰":
            g, ok = "관찰", False
        else:
            g, ok = "탈락", False
        final_grade.append(g)
        final_pass.append("✅" if ok else "❌")
    result["최종등급"] = final_grade
    result["최종통과"] = final_pass
    return result


def show_saved_report():
    path = Path("reports/latest_validation.csv")
    if not path.exists():
        st.info("첫 자동 시장 스캔 결과를 기다리는 중입니다. 수동 검증은 지금도 실행할 수 있습니다.")
        return
    try:
        auto = pd.read_csv(path)
        if auto.empty:
            return
        report_version = str(auto["엔진버전"].iloc[0]) if "엔진버전" in auto.columns else "legacy"
        if report_version != EXPECTED_ENGINE_VERSION:
            st.warning(f"저장된 자동 리포트는 이전 엔진({report_version}) 결과라 숨겼습니다. 새 {EXPECTED_ENGINE_VERSION} 스캔 결과를 기다리는 중입니다.")
            return
        run_at = str(auto["실행시각UTC"].iloc[0]) if "실행시각UTC" in auto.columns else "기록 없음"
        strict = auto[auto["최종통과"] == "✅"] if "최종통과" in auto.columns else auto.iloc[0:0]
        watch = auto[auto["최종등급"].isin(["A", "B", "관찰"])] if "최종등급" in auto.columns else auto.iloc[0:0]
        with st.expander("📡 최신 자동 시장 스캔", expanded=True):
            st.caption(f"엔진 {report_version} · 마지막 자동 실행(UTC): {run_at}")
            a1,a2,a3,a4 = st.columns(4)
            a1.metric("자동 검사", f"{len(auto)}개")
            a2.metric("A 통과", f"{len(strict)}개")
            a3.metric("관찰 이상", f"{len(watch)}개")
            a4.metric("최고 TEST", pct(pd.to_numeric(auto.get("TEST수익"), errors="coerce").max()))
            if len(strict):
                st.success("자동 스캔에서 A등급 후보가 발견됐습니다. 실제 자금 투입 전 모의검증은 계속 필요합니다.")
            elif len(watch):
                st.warning("A등급은 없고 관찰 후보만 있습니다. 현재 행동은 실매수 보류입니다.")
            else:
                st.error("자동 스캔 기준으로 통계적 후보가 없습니다. 현재 행동은 관망입니다.")
            display = auto.copy()
            for col in ["TEST수익","최근63일","MDD","승률"]:
                if col in display.columns:
                    display[col] = pd.to_numeric(display[col], errors="coerce").apply(pct)
            for col in ["PF","샤프","타이밍p","다중검정q","점수"]:
                if col in display.columns:
                    display[col] = pd.to_numeric(display[col], errors="coerce").apply(lambda x: "-" if not np.isfinite(x) else f"{x:.3f}")
            cols = [c for c in ["최종통과","최종등급","시장","종목","코드","선택전략","TEST수익","최근63일","MDD","TEST거래수","PF","샤프","타이밍p","다중검정q","탈락사유"] if c in display.columns]
            st.dataframe(display[cols], use_container_width=True, hide_index=True)
    except Exception as e:
        st.warning(f"저장된 자동 리포트를 읽지 못했습니다: {e}")


st.title("🧠 APEX Autonomous Validation v8.2")
st.caption("다음날 시가 체결 · 자가 테스트 · 다중전략 경쟁 · purged OOF AI · 완전 분리 TEST · 순환 타이밍 검정 · 다중검정 보정")
st.warning("연구·모의투자용입니다. A등급도 미래 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")

checks = run_self_tests()
if checks and all(checks.values()):
    st.success(f"엔진 자가검증 통과 · {sum(checks.values())}/{len(checks)} 테스트 정상")
else:
    st.error(f"엔진 자가검증 실패: {checks}")
    st.stop()

show_saved_report()

with st.sidebar:
    st.header("자동 검증 범위")
    market_choice = st.selectbox("시장", ["한국 40종목", "미국 40종목", "직접 입력"])
    period = st.selectbox("기간", ["5y", "10y"], index=0)
    max_count = st.slider("검사 종목", 4, 30, 12, 2)
    fast_mode = st.toggle("무료 서버 빠른 모드", value=True)
    future = st.slider("AI 예측 거래일", 2, 10, 5)
    target_pct = st.slider("AI 상승 기준(%)", 0.0, 5.0, 1.0, .1) / 100
    fee = st.slider("편도 비용(%)", 0.05, 0.30, 0.15, .01) / 100
    custom = st.text_area("직접 종목코드", "005930.KS,000660.KS,NVDA,AAPL")
    run = st.button("🚀 자율 검증 실행", type="primary")

if not run:
    st.info("자동 리포트는 평일 아침 갱신됩니다. 필요할 때만 왼쪽 메뉴에서 수동 자율 검증을 실행하세요.")
    st.stop()

if market_choice == "한국 40종목":
    universe = list(KOREA.items())[:max_count]
    benchmark = "^KS11"
elif market_choice == "미국 40종목":
    universe = list(USA.items())[:max_count]
    benchmark = "SPY"
else:
    codes = [x.strip().upper() for x in custom.split(",") if x.strip()][:max_count]
    universe = [(x, x) for x in codes]
    benchmark = "^KS11" if any(x.endswith((".KS", ".KQ")) for x in codes) else "SPY"

progress = st.progress(0, text="시장 데이터 준비 중...")
rows, errors = [], []
try:
    market = download_one(benchmark, period)
    for i, (name, ticker) in enumerate(universe):
        progress.progress(i / len(universe), text=f"{i+1}/{len(universe)} {name} 자동 검증 중")
        try:
            raw = download_one(ticker, period)
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

result = apply_portfolio_control(pd.DataFrame(rows))
result = result.sort_values(["최종통과", "점수"], ascending=[True, False]).reset_index(drop=True)
strict = result[result["최종통과"] == "✅"]
watch = result[result["최종등급"].isin(["A", "B", "관찰"])]

c1,c2,c3,c4=st.columns(4)
c1.metric("검사",f"{len(result)}개")
c2.metric("A 통과",f"{len(strict)}개")
c3.metric("관찰 이상",f"{len(watch)}개")
c4.metric("최고 TEST",pct(result["TEST수익"].max()))

if len(strict):
    st.success("A등급 후보가 있습니다. 다만 실제 자금 투입 전에는 일정 기간 모의투자가 필요합니다.")
elif len(watch):
    st.warning("A등급은 없고 관찰 후보만 있습니다. 앱의 행동은 '실매수 보류'입니다.")
else:
    st.error("통계적으로 남은 후보가 없습니다. 앱의 행동은 '관망'입니다.")

show=result.copy()
for col in ["사전중앙수익","사전양수비율","TEST수익","TEST구간양수비율","TEST구간중앙수익","최근63일","매수보유","MDD","승률"]:
    show[col]=show[col].apply(pct)
for col in ["PF","샤프","AI OOF AUC","AI TEST AUC","타이밍p","다중검정q","점수"]:
    show[col]=show[col].apply(lambda x:"-" if not np.isfinite(x) else f"{x:.3f}")

cols=[
    "최종통과","최종등급","종목","코드","선택전략","사전중앙수익","TEST수익","TEST구간양수비율",
    "최근63일","MDD","TEST거래수","승률","PF","샤프","타이밍p","다중검정q",
    "AI OOF AUC","AI TEST AUC","탈락사유","점수"
]
st.dataframe(show[cols],use_container_width=True,hide_index=True)

st.subheader("선택 전략 분포")
st.bar_chart(result["선택전략"].value_counts())

st.subheader("상위 후보 TEST 수익")
st.bar_chart(result.set_index("종목")[["TEST수익"]].head(12)*100)

st.download_button(
    "검증 결과 CSV",
    result.to_csv(index=False).encode("utf-8-sig"),
    "apex_v8_validation.csv",
    "text/csv",
)

if errors:
    with st.expander(f"분석 제외 {len(errors)}개"):
        st.code("\n".join(errors))
