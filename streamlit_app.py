import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit

st.set_page_config(page_title="APEX AI 주식매매 봇 v2", page_icon="📈", layout="wide")
st.markdown("""
<style>
.block-container{padding:1rem .8rem 2rem;max-width:1200px}
h1{font-size:clamp(1.5rem,6vw,2.3rem)!important}
.stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
[data-testid="stMetricValue"]{font-size:clamp(1.1rem,5vw,1.8rem)}
@media(max-width:768px){
[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}
[data-testid="stSidebar"]{min-width:88vw;max-width:88vw}
}
</style>
""", unsafe_allow_html=True)

FEATURES = [
    "ret1","ret3","ret5","ema8_21","ema21_55","ema55_200",
    "rsi","macd_pct","hist_pct","atr_pct","bb_pos","vol_ratio",
    "volatility","range_pct","close_location"
]

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker, period, interval):
    d = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False, threads=False)
    if d is None or d.empty:
        raise ValueError("가격 데이터를 받지 못했습니다. 종목코드를 확인하세요.")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    need = ["Open","High","Low","Close","Volume"]
    if any(c not in d.columns for c in need):
        raise ValueError("OHLCV 데이터 형식이 올바르지 않습니다.")
    d = d[need].dropna()
    if len(d) < 450:
        raise ValueError(f"데이터가 {len(d)}개뿐입니다. 기간을 늘리거나 일봉을 선택하세요.")
    return d

def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    x = s.diff()
    g = x.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    l = (-x.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return (100 - 100/(1 + g/l.replace(0, np.nan))).fillna(50)

def atr(d, n=14):
    pc = d.Close.shift(1)
    tr = pd.concat([d.High-d.Low,(d.High-pc).abs(),(d.Low-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def make_features(raw, future, target_pct):
    d = raw.copy()
    for n in [8,21,55,200]:
        d[f"ema{n}"] = ema(d.Close, n)
    d["rsi"] = rsi(d.Close)
    macd = ema(d.Close,12) - ema(d.Close,26)
    signal = ema(macd,9)
    d["macd_pct"] = macd / d.Close
    d["hist_pct"] = (macd-signal) / d.Close
    d["atr"] = atr(d)
    d["atr_pct"] = d.atr / d.Close
    mid = d.Close.rolling(20).mean()
    sd = d.Close.rolling(20).std()
    lo, hi = mid-2*sd, mid+2*sd
    d["bb_pos"] = (d.Close-lo) / (hi-lo).replace(0,np.nan)
    d["vol_ratio"] = d.Volume / d.Volume.rolling(20).mean()
    d["volatility"] = d.Close.pct_change().rolling(10).std()
    d["range_pct"] = (d.High-d.Low) / d.Close
    d["close_location"] = (d.Close-d.Low) / (d.High-d.Low).replace(0,np.nan)
    d["ret1"] = d.Close.pct_change()
    d["ret3"] = d.Close.pct_change(3)
    d["ret5"] = d.Close.pct_change(5)
    d["ema8_21"] = d.ema8/d.ema21-1
    d["ema21_55"] = d.ema21/d.ema55-1
    d["ema55_200"] = d.ema55/d.ema200-1
    d["future_return"] = d.Close.shift(-future)/d.Close-1
    d["target"] = (d.future_return > target_pct).astype(int)
    return d.replace([np.inf,-np.inf],np.nan).dropna()

def new_model(seed=42):
    return RandomForestClassifier(n_estimators=500,max_depth=6,min_samples_leaf=10,max_features="sqrt",class_weight="balanced_subsample",oob_score=True,n_jobs=-1,random_state=seed)

def time_series_auc(data):
    if len(data) < 500:
        return np.nan
    splitter = TimeSeriesSplit(n_splits=4)
    scores = []
    for fold, (tr_idx, va_idx) in enumerate(splitter.split(data)):
        tr, va = data.iloc[tr_idx], data.iloc[va_idx]
        if tr.target.nunique() < 2 or va.target.nunique() < 2:
            continue
        m = new_model(100 + fold)
        m.fit(tr[FEATURES], tr.target)
        p = m.predict_proba(va[FEATURES])[:,1]
        scores.append(roc_auc_score(va.target,p))
    return float(np.mean(scores)) if scores else np.nan

def choose_threshold(model, desired_signal_rate, manual_threshold, auto_mode):
    if not auto_mode:
        return float(manual_threshold)
    oob = model.oob_decision_function_
    if oob is None or len(oob) == 0:
        return float(manual_threshold)
    p = oob[:,1]
    p = p[np.isfinite(p)]
    if len(p) < 100:
        return float(manual_threshold)
    return float(np.quantile(p, np.clip(1-desired_signal_rate, 0.50, 0.95)))

def backtest(test, initial_cash, fee, slip, risk, threshold, stop_atr, take_atr, max_bars):
    cash = float(initial_cash)
    shares = 0
    entry = stop = take = 0.0
    entry_i = None
    entry_fee = 0.0
    trades, curve = [], []
    signal_prob = test.probability.shift(1)
    signal_trend = ((test.Close.shift(1) > test.ema55.shift(1)) & (test.ema8.shift(1) > test.ema21.shift(1)) & (test.rsi.shift(1).between(43,76)) & (test.vol_ratio.shift(1) >= 0.55))
    for i, (dt,row) in enumerate(test.iterrows()):
        o,h,l,c,a = map(float,[row.Open,row.High,row.Low,row.Close,row.atr])
        p = float(signal_prob.iloc[i]) if pd.notna(signal_prob.iloc[i]) else np.nan
        if shares:
            reason, px = None, c
            if l <= stop:
                reason, px = "ATR 손절", stop*(1-slip)
            elif h >= take:
                reason, px = "ATR 익절", take*(1-slip)
            elif i-entry_i >= max_bars:
                reason, px = "최대 보유기간", c*(1-slip)
            elif pd.notna(p) and p < max(0.40, threshold-0.12):
                reason, px = "AI 약화", c*(1-slip)
            elif c < float(row.ema21):
                reason, px = "추세 이탈", c*(1-slip)
            if reason:
                gross = shares*px
                exit_fee = gross*fee
                cash += gross-exit_fee
                pnl = gross-exit_fee-(shares*entry)-entry_fee
                trades.append({"진입일":test.index[entry_i],"청산일":dt,"진입가":entry,"청산가":px,"수량":shares,"손익":pnl,"수익률":pnl/(shares*entry+entry_fee),"청산사유":reason})
                shares = 0
        if not shares and i > 0 and bool(signal_trend.iloc[i]) and pd.notna(p) and p >= threshold and a > 0:
            risk_cash = cash*risk
            risk_per_share = stop_atr*a
            qty_by_risk = int(risk_cash/risk_per_share) if risk_per_share > 0 else 0
            buy_px = o*(1+slip)
            qty_by_cash = int(cash/(buy_px*(1+fee)))
            qty = max(0,min(qty_by_risk,qty_by_cash))
            if qty > 0:
                cost = qty*buy_px
                buy_fee = cost*fee
                if cost+buy_fee <= cash:
                    cash -= cost+buy_fee
                    shares = qty
                    entry = buy_px
                    entry_fee = buy_fee
                    entry_i = i
                    stop = entry-stop_atr*a
                    take = entry+take_atr*a
        curve.append({"Date":dt,"Equity":cash+shares*c})
    if shares:
        px = float(test.Close.iloc[-1])*(1-slip)
        gross = shares*px
        exit_fee = gross*fee
        cash += gross-exit_fee
        pnl = gross-exit_fee-(shares*entry)-entry_fee
        trades.append({"진입일":test.index[entry_i],"청산일":test.index[-1],"진입가":entry,"청산가":px,"수량":shares,"손익":pnl,"수익률":pnl/(shares*entry+entry_fee),"청산사유":"테스트 종료"})
        curve[-1]["Equity"] = cash
    eq = pd.DataFrame(curve).set_index("Date")
    tr = pd.DataFrame(trades)
    total = eq.Equity.iloc[-1]/initial_cash-1
    buyhold = test.Close.iloc[-1]/test.Open.iloc[0]-1
    mdd = (eq.Equity/eq.Equity.cummax()-1).min()
    rr = eq.Equity.pct_change().dropna()
    sharpe = np.sqrt(252)*rr.mean()/rr.std() if len(rr)>2 and rr.std()>0 else 0.0
    wr = pf = avg = np.nan
    if len(tr):
        wins = tr[tr.손익>0]
        losses = tr[tr.손익<=0]
        wr = len(wins)/len(tr)
        avg = tr.수익률.mean()
        if len(losses) and abs(losses.손익.sum())>0:
            pf = wins.손익.sum()/abs(losses.손익.sum())
    return eq,tr,{"return":float(total),"buyhold":float(buyhold),"excess":float(total-buyhold),"mdd":float(mdd),"sharpe":float(sharpe),"trades":len(tr),"winrate":wr,"pf":pf,"avg":avg,"final":float(eq.Equity.iloc[-1])}

def pct(x):
    return "N/A" if x is None or not np.isfinite(x) else f"{x*100:,.2f}%"

st.title("📈 APEX AI 주식매매 봇 v2")
st.caption("휴대폰용 · 다음 봉 진입 · 시간순 검증 · 수수료/슬리피지 반영")
st.warning("연구·모의투자용입니다. 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")

with st.sidebar:
    st.header("종목 및 데이터")
    ticker = st.text_input("종목코드","005930.KS",help="삼성전자 005930.KS / SK하이닉스 000660.KS / 애플 AAPL").strip().upper()
    interval = st.selectbox("봉 간격",["1d","1h","30m","15m"])
    periods = {"1d":["2y","5y","10y","max"],"1h":["3mo","6mo","1y","2y"],"30m":["3mo","6mo"],"15m":["3mo","6mo"]}
    period = st.selectbox("데이터 기간",periods[interval],index=min(1,len(periods[interval])-1))
    st.header("AI 설정")
    train_ratio = st.slider("학습 비율",.60,.85,.70,.05)
    future = st.slider("미래 봉 수",1,10,3)
    target = st.number_input("상승 판정 기준(%)",-.5,5.,.2,.1)
    auto_threshold = st.toggle("매수 확률 자동 보정",value=True)
    desired_rate = st.slider("목표 신호 비율",.05,.35,.18,.01)
    manual_threshold = st.slider("수동 매수 확률",.45,.75,.55,.01,disabled=auto_threshold)
    st.header("위험관리")
    initial = st.number_input("초기자금(원)",100000,1000000000,10000000,100000)
    risk = st.slider("1회 허용손실(%)",.1,2.,.5,.1)
    stop = st.slider("손절 ATR",.5,3.,1.4,.1)
    take = st.slider("익절 ATR",1.,6.,2.8,.1)
    maxbars = st.slider("최대 보유 봉",2,50,15)
    fee = st.number_input("편도 비용(%)",0.,1.,.10,.01)
    slip = st.number_input("슬리피지(%)",0.,1.,.05,.01)
    run = st.button("🚀 AI 학습 및 백테스트",type="primary")

if not run:
    st.info("왼쪽 위 메뉴를 열어 종목과 설정을 고른 뒤 실행 버튼을 누르세요.")
    st.stop()

try:
    with st.spinner("데이터 수집·시간순 검증·백테스트 중..."):
        raw = load_data(ticker,period,interval)
        data = make_features(raw,future,target/100)
        cut = int(len(data)*train_ratio)
        train = data.iloc[:cut].copy()
        test = data.iloc[cut:].copy()
        if len(train)<300 or len(test)<100:
            raise ValueError(f"학습 {len(train)}개, 검증 {len(test)}개입니다. 더 긴 기간을 선택하세요.")
        cv_auc = time_series_auc(train)
        model = new_model()
        model.fit(train[FEATURES],train.target)
        threshold = choose_threshold(model,desired_rate,manual_threshold,auto_threshold)
        test["probability"] = model.predict_proba(test[FEATURES])[:,1]
        pred = (test.probability>=threshold).astype(int)
        accuracy = accuracy_score(test.target,pred)
        auc = roc_auc_score(test.target,test.probability) if test.target.nunique()>1 else np.nan
        eq,tr,m = backtest(test,float(initial),fee/100,slip/100,risk/100,threshold,stop,take,maxbars)
    st.success(f"완료 · 학습 {len(train):,}개 / 검증 {len(test):,}개 / 적용 확률 {threshold:.3f}")
    a,b,c,d = st.columns(4)
    a.metric("검증 ROC-AUC",f"{auc:.3f}" if np.isfinite(auc) else "N/A")
    b.metric("시계열 CV AUC",f"{cv_auc:.3f}" if np.isfinite(cv_auc) else "N/A")
    c.metric("전략 수익률",pct(m["return"]))
    d.metric("매수보유",pct(m["buyhold"]))
    a,b,c,d = st.columns(4)
    a.metric("초과 수익",pct(m["excess"]))
    b.metric("최대낙폭",pct(m["mdd"]))
    c.metric("거래 수",f"{m['trades']}회")
    d.metric("샤프지수",f"{m['sharpe']:.2f}")
    if m["trades"] >= 5:
        a,b,c = st.columns(3)
        a.metric("승률",pct(m["winrate"]))
        b.metric("평균 거래수익",pct(m["avg"]))
        c.metric("Profit Factor",f"{m['pf']:.2f}" if np.isfinite(m["pf"]) else "계산 불가")
    else:
        st.warning("거래가 5회 미만이라 승률과 Profit Factor는 표시하지 않습니다. 통계적 의미가 없습니다.")
    if np.isfinite(auc) and auc < 0.50:
        st.error("AI 판별력이 무작위보다 낮습니다. 이 결과는 실거래 후보가 아닙니다.")
    elif m["trades"] < 20:
        st.warning("거래 표본이 20회 미만입니다. 기간·종목을 늘려 추가 검증해야 합니다.")
    elif m["pf"] is not None and np.isfinite(m["pf"]) and m["pf"] >= 1.3 and m["mdd"] >= -0.12 and m["excess"] > 0:
        st.success("1차 연구 기준을 통과했습니다. 그래도 최소 8주 모의투자가 필요합니다.")
    else:
        st.warning("현재 설정은 1차 연구 기준을 통과하지 못했습니다.")
    chart = pd.DataFrame({"전략":eq.Equity/eq.Equity.iloc[0]*100,"매수보유":test.Close/test.Close.iloc[0]*100})
    st.line_chart(chart)
    st.subheader("AI가 중요하게 본 지표")
    imp = pd.DataFrame({"지표":FEATURES,"중요도":model.feature_importances_}).sort_values("중요도",ascending=False)
    st.bar_chart(imp.set_index("지표"))
    st.subheader("거래내역")
    if tr.empty:
        st.warning("조건을 만족한 거래가 없습니다.")
    else:
        show = tr.copy()
        show["수익률"] = (show["수익률"]*100).round(2).astype(str)+"%"
        st.dataframe(show,use_container_width=True,hide_index=True)
        st.download_button("거래내역 CSV 다운로드",tr.to_csv(index=False).encode("utf-8-sig"),f"{ticker}_trades.csv","text/csv")
except Exception as e:
    st.error(f"실행 오류: {e}")
