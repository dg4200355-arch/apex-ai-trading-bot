import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

from engine import analyze_frame, make_features, run_self_tests
from market_data import download_ohlcv

PRIMARY_VERSION = "8.5-frozen-primary"
CONFIRM_VERSION = "8.5-frozen-confirm"
TRACKER_VERSION = "paper-forward-1.2-frozen-admission"
GATE_VERSION = "promotion-gate-1.3-frozen-admission"
PORTFOLIO_VERSION = "portfolio-gate-1.1-cluster-leader"

st.set_page_config(page_title="APEX Autonomous Validation v8.6", page_icon="🧠", layout="wide")
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
    "에코프로":"086520.KQ","알테오젠":"196170.KQ","HLB":"028300.KQ","리노공업":"058470.KQ",
}
USA = {
    "Apple":"AAPL","Microsoft":"MSFT","NVIDIA":"NVDA","Amazon":"AMZN","Meta":"META","Alphabet":"GOOGL",
    "Tesla":"TSLA","Broadcom":"AVGO","AMD":"AMD","Netflix":"NFLX","JPMorgan":"JPM","Eli Lilly":"LLY",
    "Berkshire":"BRK-B","Visa":"V","Mastercard":"MA","Walmart":"WMT","Costco":"COST","Oracle":"ORCL",
    "Salesforce":"CRM","Adobe":"ADBE","Palantir":"PLTR","Micron":"MU","Qualcomm":"QCOM","Intel":"INTC",
    "Cisco":"CSCO","IBM":"IBM","Coca-Cola":"KO","PepsiCo":"PEP","McDonalds":"MCD","Nike":"NKE",
    "ExxonMobil":"XOM","Chevron":"CVX","UnitedHealth":"UNH","Johnson&Johnson":"JNJ","Merck":"MRK","AbbVie":"ABBV",
    "HomeDepot":"HD","Boeing":"BA","Caterpillar":"CAT","GoldmanSachs":"GS",
}


def pct(x):
    try:
        return "-" if not np.isfinite(float(x)) else f"{float(x)*100:.2f}%"
    except Exception:
        return "-"


def num(x, digits=3):
    try:
        return "-" if not np.isfinite(float(x)) else f"{float(x):.{digits}f}"
    except Exception:
        return "-"


def safe_csv(path):
    try:
        p = Path(path)
        return pd.read_csv(p) if p.exists() and p.stat().st_size else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def bh_qvalues(values):
    p = np.asarray(values, dtype=float)
    q = np.full(len(p), np.nan)
    valid = np.isfinite(p)
    if not valid.any(): return q
    pv = p[valid]; order = np.argsort(pv); ranked = pv[order]
    raw = ranked * len(ranked) / np.arange(1, len(ranked)+1)
    adj = np.minimum.accumulate(raw[::-1])[::-1]
    out = np.empty(len(ranked)); out[order] = np.clip(adj, 0, 1)
    q[np.where(valid)[0]] = out
    return q


def manual_control(df):
    out = df.copy(); out["다중검정q"] = bh_qvalues(out["타이밍p"].to_numpy())
    grades, passed = [], []
    for _, r in out.iterrows():
        grade, q = r["등급"], r["다중검정q"]
        if grade == "A" and np.isfinite(q) and q <= .20: g, ok = "A", True
        elif grade in {"A","B"}: g, ok = "B", False
        elif grade == "관찰": g, ok = "관찰", False
        else: g, ok = "탈락", False
        grades.append(g); passed.append("✅" if ok else "❌")
    out["최종등급"] = grades; out["최종통과"] = passed
    return out


def render_primary():
    df = safe_csv("reports/latest_validation.csv")
    with st.expander("① 📡 80종목 전체 자동 스캔 · 전략 동결", expanded=True):
        if df.empty: st.info("자동 스캔 결과를 기다리는 중입니다."); return
        version = str(df.get("엔진버전",pd.Series(["legacy"])).iloc[0])
        if version != PRIMARY_VERSION: st.warning(f"이전 결과 {version} · {PRIMARY_VERSION} 대기 중"); return
        watch = df[df["최종등급"].isin(["A","B","관찰"])]
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("검정패밀리","80개"); c2.metric("분석",f"{len(df)}개")
        c3.metric("A 통과",f"{(df['최종통과']=='✅').sum()}개"); c4.metric("2차 대상",f"{len(watch)}개")
        st.caption(f"{version} · 파라미터/기준일 동결 · OHLCV 무결성 검사")
        show = df.copy()
        for c in ["TEST수익","MDD"]:
            if c in show: show[c] = pd.to_numeric(show[c],errors="coerce").apply(pct)
        for c in ["PF","샤프","타이밍p","다중검정q"]:
            if c in show: show[c] = pd.to_numeric(show[c],errors="coerce").apply(num)
        cols=[c for c in ["최종등급","시장","종목","선택전략","전략파라미터","데이터기준일","TEST수익","MDD","TEST거래수","PF","샤프","타이밍p","다중검정q","탈락사유"] if c in show]
        st.dataframe(show[cols],use_container_width=True,hide_index=True)


def render_confirmation():
    df = safe_csv("reports/latest_confirmation.csv")
    with st.expander("② 🧪 동일 파라미터 2차 재현·스트레스", expanded=True):
        if df.empty: st.info("2차 결과를 기다리는 중입니다."); return
        version = str(df.get("확인엔진",pd.Series(["legacy"])).iloc[0])
        if version != CONFIRM_VERSION: st.warning(f"이전 결과 {version} · {CONFIRM_VERSION} 대기 중"); return
        confirmed = df[df["2차통과"]=="✅"]
        c1,c2,c3 = st.columns(3)
        c1.metric("2차 검사",f"{len(df)}개"); c2.metric("확인후보",f"{len(confirmed)}개"); c3.metric("엔진",version)
        show = df.copy()
        for c in ["1차TEST수익","재현TEST수익","재현오차","비용중앙수익","파라미터양수비율","10년양수비율","10년중앙수익"]:
            if c in show: show[c] = pd.to_numeric(show[c],errors="coerce").apply(pct)
        cols=[c for c in ["2차통과","2차등급","종목","전략","전략파라미터","1차데이터기준일","1차TEST수익","재현TEST수익","재현오차","비용중앙수익","파라미터양수비율","10년양수비율","10년중앙수익","10년거래수","보류사유"] if c in show]
        st.dataframe(show[cols],use_container_width=True,hide_index=True)


def render_paper():
    df = safe_csv("reports/paper_forward.csv")
    with st.expander("③ 🧾 동결재검증 전진 모의", expanded=True):
        if df.empty: st.info("전진 모의 후보가 아직 없습니다."); return
        if "시각UTC" in df: df = df.sort_values("시각UTC")
        latest = df.drop_duplicates("코드",keep="last")
        c1,c2,c3 = st.columns(3)
        c1.metric("추적",f"{len(latest)}개")
        c2.metric("완료거래",f"{int(pd.to_numeric(latest.get('완료거래'),errors='coerce').fillna(0).sum())}회")
        c3.metric("최고 전진수익",pct(pd.to_numeric(latest.get("전진누적수익"),errors="coerce").max()))
        tracker = str(latest.get("트래커",pd.Series(["-"])).iloc[-1])
        st.caption(f"{tracker} · FROZEN_VERIFIED만 승격 가능 · 누락 거래일 자동 재생")
        show = latest.copy()
        for c in ["승률","전진누적수익","전진MDD"]:
            if c in show: show[c] = pd.to_numeric(show[c],errors="coerce").apply(pct)
        if "PF" in show: show["PF"] = pd.to_numeric(show["PF"],errors="coerce").apply(lambda x:num(x,2))
        cols=[c for c in ["동결검증","종목","전략","신호기준일","종가신호","현재포지션","관측거래일","완료거래","승률","PF","전진누적수익","전진MDD","업데이트","오류"] if c in show]
        st.dataframe(show[cols],use_container_width=True,hide_index=True)


def render_gate():
    df = safe_csv("reports/promotion_status.csv")
    with st.expander("④ 🛡️ 최종 전진증거 게이트", expanded=True):
        if df.empty: st.info("최종 게이트 결과를 기다리는 중입니다."); return
        gate = str(df.get("게이트",pd.Series(["legacy"])).iloc[0])
        if gate != GATE_VERSION: st.warning(f"이전 게이트 {gate} · {GATE_VERSION} 대기 중"); return
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("추적",f"{len(df)}개"); c2.metric("검증완료",f"{(df['최종상태']=='전진검증완료').sum()}개")
        c3.metric("관찰중",f"{(df['최종상태']=='관찰중').sum()}개"); c4.metric("전진실패",f"{(df['최종상태']=='전진실패').sum()}개")
        st.caption(f"{gate} · 동결재검증 + 60거래일·5완료거래 + 비용/부트스트랩/sign-test/BH")
        show = df.copy()
        for c in ["전진누적수익","전진MDD","승률","비용스트레스수익","부트스트랩양수확률"]:
            if c in show: show[c] = pd.to_numeric(show[c],errors="coerce").apply(pct)
        for c in ["PF","방향성p","전진다중검정q"]:
            if c in show: show[c] = pd.to_numeric(show[c],errors="coerce").apply(num)
        cols=[c for c in ["승격가능","최종상태","동결검증","종목","전략","관측거래일","완료거래","전진누적수익","전진MDD","승률","PF","비용스트레스수익","부트스트랩양수확률","방향성p","전진다중검정q","현재포지션","대기조건"] if c in show]
        st.dataframe(show[cols],use_container_width=True,hide_index=True)


def render_portfolio():
    df = safe_csv("reports/portfolio_risk.csv")
    with st.expander("⑤ 🧩 포트폴리오 중복위험·군집대표 게이트", expanded=True):
        if df.empty: st.info("포트폴리오 결과를 기다리는 중입니다."); return
        version = str(df.get("게이트",pd.Series(["legacy"])).iloc[0])
        if version != PORTFOLIO_VERSION: st.warning(f"이전 결과 {version} · {PORTFOLIO_VERSION} 대기 중"); return
        corr = pd.to_numeric(df.get("최대상관",pd.Series(dtype=float)),errors="coerce")
        high = int((df.get("중복위험",pd.Series(dtype=str))=="⚠️").sum())
        allowed = int((df.get("포트폴리오허용",pd.Series(dtype=str))=="✅").sum())
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("추적",f"{len(df)}개"); c2.metric("고상관 경고",f"{high}개")
        c3.metric("포트폴리오 허용",f"{allowed}개"); c4.metric("최대 상관","-" if corr.dropna().empty else f"{corr.max():.3f}")
        st.caption(f"{version} · 상관 0.80 이상 군집 · 여러 종목이 최종통과하면 forward evidence가 가장 강한 1개만 ⭐ 대표")
        show = df.copy()
        if "최대상관" in show: show["최대상관"] = pd.to_numeric(show["최대상관"],errors="coerce").apply(num)
        cols=[c for c in ["포트폴리오허용","최종상태","동결검증","종목","시장","전략","상관군집","군집대표","군집대표종목","최대상관","최대상관대상","공통거래일","중복위험","포트폴리오대기조건","데이터오류"] if c in show]
        st.dataframe(show[cols],use_container_width=True,hide_index=True)


st.title("🧠 APEX Autonomous Validation v8.6")
st.caption("80종목 전체검정 → 파라미터 동결 2차 → 전진모의 → 최종 통계 → 상관군집 대표선택")
st.warning("연구·모의투자용입니다. 미래 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")
checks = run_self_tests()
if not checks or not all(checks.values()): st.error(f"엔진 자가검증 실패: {checks}"); st.stop()
st.success(f"엔진 자가검증 통과 · {sum(checks.values())}/{len(checks)}")
render_primary(); render_confirmation(); render_paper(); render_gate(); render_portfolio()

with st.sidebar:
    st.header("수동 검증")
    market_choice=st.selectbox("시장",["한국 40종목","미국 40종목","직접 입력"])
    period=st.selectbox("기간",["5y","10y"],index=0)
    max_count=st.slider("검사 종목",4,30,12,2)
    fast_mode=st.toggle("무료 서버 빠른 모드",value=True)
    future=st.slider("AI 예측 거래일",2,10,5)
    target_pct=st.slider("AI 상승 기준(%)",0.0,5.0,1.0,.1)/100
    fee=st.slider("편도 비용(%)",0.05,0.30,0.15,.01)/100
    custom=st.text_area("직접 종목코드","005930.KS,000660.KS,NVDA,AAPL")
    run=st.button("🚀 수동 검증",type="primary")

if not run:
    st.info("자동 파이프라인은 평일마다 80종목 전체를 ①→⑤ 순서로 갱신합니다.")
    st.stop()

if market_choice=="한국 40종목": universe=list(KOREA.items())[:max_count]; benchmark="^KS11"
elif market_choice=="미국 40종목": universe=list(USA.items())[:max_count]; benchmark="SPY"
else:
    codes=[x.strip().upper() for x in custom.split(",") if x.strip()][:max_count]
    universe=[(x,x) for x in codes]
    benchmark="^KS11" if any(x.endswith((".KS",".KQ")) for x in codes) else "SPY"

progress=st.progress(0,text="데이터 품질검사 포함 검증 준비 중...")
rows=[]; errors=[]
try:
    market=download_ohlcv(benchmark,period=period)
    for i,(name,ticker) in enumerate(universe):
        progress.progress(i/len(universe),text=f"{i+1}/{len(universe)} {name}")
        try:
            raw=download_ohlcv(ticker,period=period)
            data=make_features(raw,market,future,target_pct)
            rows.append(analyze_frame(name,ticker,data,future,fee,fast_mode))
        except Exception as e: errors.append(f"{name}: {e}")
    progress.progress(1.0,text="검증 완료")
except Exception as e:
    st.error(f"시장 데이터 오류: {e}"); st.stop()

if not rows:
    st.error("분석 가능한 종목이 없습니다.")
    if errors: st.code("\n".join(errors))
    st.stop()

result=manual_control(pd.DataFrame(rows)).sort_values("점수",ascending=False).reset_index(drop=True)
c1,c2,c3=st.columns(3)
c1.metric("검사",f"{len(result)}개"); c2.metric("A 통과",f"{(result['최종통과']=='✅').sum()}개"); c3.metric("최고 TEST",pct(result["TEST수익"].max()))
show=result.copy()
for c in ["TEST수익","최근63일","MDD","승률"]:
    if c in show: show[c]=show[c].apply(pct)
for c in ["PF","샤프","타이밍p","다중검정q","점수"]:
    if c in show: show[c]=show[c].apply(num)
cols=[c for c in ["최종통과","최종등급","종목","코드","선택전략","TEST수익","최근63일","MDD","TEST거래수","승률","PF","샤프","타이밍p","다중검정q","탈락사유","점수"] if c in show]
st.dataframe(show[cols],use_container_width=True,hide_index=True)
st.download_button("검증 결과 CSV",result.to_csv(index=False).encode("utf-8-sig"),"apex_v86_manual_validation.csv","text/csv")
if errors:
    with st.expander(f"분석 제외 {len(errors)}개"): st.code("\n".join(errors))
