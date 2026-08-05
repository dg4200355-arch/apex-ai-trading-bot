import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="APEX AI 주식매매 봇 v3", page_icon="📈", layout="wide")
st.markdown("""
<style>
.block-container{padding:1rem .8rem 2rem;max-width:1200px}
h1{font-size:clamp(1.5rem,6vw,2.3rem)!important}
.stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
[data-testid="stMetricValue"]{font-size:clamp(1.05rem,5vw,1.75rem)}
@media(max-width:768px){[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}[data-testid="stSidebar"]{min-width:88vw;max-width:88vw}}
</style>
""", unsafe_allow_html=True)

FEATURES=["ret1","ret3","ret5","ret10","ema8_21","ema21_55","ema55_200","rsi","macd_pct","hist_pct","atr_pct","bb_pos","vol_ratio","volatility","range_pct","close_location","market_ret1","market_ret5","market_trend"]

@st.cache_data(ttl=3600,show_spinner=False)
def download_one(ticker,period,interval):
    d=yf.download(ticker,period=period,interval=interval,auto_adjust=True,progress=False,threads=False)
    if d is None or d.empty: raise ValueError(f"{ticker} 데이터를 받지 못했습니다.")
    if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
    d.columns=[str(c).title() for c in d.columns]
    need=["Open","High","Low","Close","Volume"]
    if any(c not in d.columns for c in need): raise ValueError("가격 데이터 형식이 올바르지 않습니다.")
    return d[need].dropna()

def benchmark_for(ticker):
    return "^KS11" if ticker.endswith((".KS",".KQ")) else "SPY"

def ema(s,n): return s.ewm(span=n,adjust=False).mean()

def rsi(s,n=14):
    x=s.diff(); g=x.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); l=(-x.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
    return (100-100/(1+g/l.replace(0,np.nan))).fillna(50)

def atr(d,n=14):
    pc=d.Close.shift(1)
    tr=pd.concat([d.High-d.Low,(d.High-pc).abs(),(d.Low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False).mean()

def make_features(raw,market,future,target_pct):
    d=raw.copy()
    for n in [8,21,55,200]: d[f"ema{n}"]=ema(d.Close,n)
    d["rsi"]=rsi(d.Close)
    macd=ema(d.Close,12)-ema(d.Close,26); sig=ema(macd,9)
    d["macd_pct"]=macd/d.Close; d["hist_pct"]=(macd-sig)/d.Close
    d["atr"]=atr(d); d["atr_pct"]=d.atr/d.Close
    mid=d.Close.rolling(20).mean(); sd=d.Close.rolling(20).std(); lo=mid-2*sd; hi=mid+2*sd
    d["bb_pos"]=(d.Close-lo)/(hi-lo).replace(0,np.nan)
    d["vol_ratio"]=d.Volume/d.Volume.rolling(20).mean()
    d["volatility"]=d.Close.pct_change().rolling(10).std()
    d["range_pct"]=(d.High-d.Low)/d.Close
    d["close_location"]=(d.Close-d.Low)/(d.High-d.Low).replace(0,np.nan)
    for n in [1,3,5,10]: d[f"ret{n}"]=d.Close.pct_change(n)
    d["ema8_21"]=d.ema8/d.ema21-1; d["ema21_55"]=d.ema21/d.ema55-1; d["ema55_200"]=d.ema55/d.ema200-1
    m=market.Close.reindex(d.index).ffill()
    d["market_ret1"]=m.pct_change(); d["market_ret5"]=m.pct_change(5); d["market_trend"]=m/ema(m,50)-1
    d["future_return"]=d.Close.shift(-future)/d.Close-1
    d["target"]=(d.future_return>target_pct).astype(int)
    return d.replace([np.inf,-np.inf],np.nan).dropna()

def models(seed=42):
    return [
        RandomForestClassifier(n_estimators=400,max_depth=6,min_samples_leaf=12,max_features="sqrt",class_weight="balanced_subsample",n_jobs=-1,random_state=seed),
        HistGradientBoostingClassifier(max_iter=180,max_depth=4,learning_rate=.04,l2_regularization=1.0,random_state=seed),
        make_pipeline(StandardScaler(),LogisticRegression(C=.25,class_weight="balanced",max_iter=1000,random_state=seed)),
    ]

def cv_weights(train):
    splitter=TimeSeriesSplit(n_splits=4); fold_scores=[[],[],[]]
    for fold,(ti,vi) in enumerate(splitter.split(train)):
        tr,va=train.iloc[ti],train.iloc[vi]
        if tr.target.nunique()<2 or va.target.nunique()<2: continue
        for j,m in enumerate(models(100+fold)):
            m.fit(tr[FEATURES],tr.target); p=m.predict_proba(va[FEATURES])[:,1]
            fold_scores[j].append(roc_auc_score(va.target,p))
    aucs=np.array([np.mean(x) if x else .5 for x in fold_scores])
    edge=np.maximum(aucs-.5,0)
    weights=edge/edge.sum() if edge.sum()>0 else np.ones(3)/3
    return aucs,weights

def fit_predict(train,test,weights):
    probs=[]; fitted=[]
    for m in models():
        m.fit(train[FEATURES],train.target); probs.append(m.predict_proba(test[FEATURES])[:,1]); fitted.append(m)
    return np.average(np.vstack(probs),axis=0,weights=weights),fitted

def choose_threshold(train_probs,signal_rate):
    return float(np.quantile(train_probs,np.clip(1-signal_rate,.55,.95)))

def backtest(test,initial,fee,slip,risk,threshold,stop_atr,take_atr,maxbars):
    cash=float(initial); shares=0; entry=entry_fee=stop=take=0.; entry_i=None; trades=[]; curve=[]
    prob=test.probability.shift(1)
    trend=(test.Close.shift(1)>test.ema55.shift(1))&(test.ema8.shift(1)>test.ema21.shift(1))&(test.market_trend.shift(1)>-.03)&test.rsi.shift(1).between(42,75)
    for i,(dt,row) in enumerate(test.iterrows()):
        o,h,l,c,a=map(float,[row.Open,row.High,row.Low,row.Close,row.atr]); p=prob.iloc[i]
        if shares:
            reason=None; px=c
            if l<=stop: reason,px="ATR 손절",stop*(1-slip)
            elif h>=take: reason,px="ATR 익절",take*(1-slip)
            elif i-entry_i>=maxbars: reason,px="최대 보유",c*(1-slip)
            elif c<float(row.ema21): reason,px="추세 이탈",c*(1-slip)
            if reason:
                gross=shares*px; ef=gross*fee; cash+=gross-ef; pnl=gross-ef-shares*entry-entry_fee
                trades.append({"진입일":test.index[entry_i],"청산일":dt,"진입가":entry,"청산가":px,"수량":shares,"손익":pnl,"수익률":pnl/(shares*entry+entry_fee),"청산사유":reason}); shares=0
        if not shares and i>0 and bool(trend.iloc[i]) and pd.notna(p) and p>=threshold and a>0:
            buy=o*(1+slip); qty=min(int(cash*risk/(stop_atr*a)),int(cash/(buy*(1+fee))))
            if qty>0:
                cost=qty*buy; bf=cost*fee
                if cost+bf<=cash:
                    cash-=cost+bf; shares=qty; entry=buy; entry_fee=bf; entry_i=i; stop=entry-stop_atr*a; take=entry+take_atr*a
        curve.append({"Date":dt,"Equity":cash+shares*c})
    if shares:
        px=float(test.Close.iloc[-1])*(1-slip); gross=shares*px; ef=gross*fee; cash+=gross-ef; pnl=gross-ef-shares*entry-entry_fee
        trades.append({"진입일":test.index[entry_i],"청산일":test.index[-1],"진입가":entry,"청산가":px,"수량":shares,"손익":pnl,"수익률":pnl/(shares*entry+entry_fee),"청산사유":"테스트 종료"}); curve[-1]["Equity"]=cash
    eq=pd.DataFrame(curve).set_index("Date"); tr=pd.DataFrame(trades)
    total=eq.Equity.iloc[-1]/initial-1; buyhold=test.Close.iloc[-1]/test.Open.iloc[0]-1; mdd=(eq.Equity/eq.Equity.cummax()-1).min(); rr=eq.Equity.pct_change().dropna(); sharpe=np.sqrt(252)*rr.mean()/rr.std() if len(rr)>2 and rr.std()>0 else 0
    wr=pf=avg=np.nan
    if len(tr):
        wins=tr[tr.손익>0]; losses=tr[tr.손익<=0]; wr=len(wins)/len(tr); avg=tr.수익률.mean(); pf=wins.손익.sum()/abs(losses.손익.sum()) if len(losses) and abs(losses.손익.sum())>0 else np.nan
    return eq,tr,{"return":total,"buyhold":buyhold,"excess":total-buyhold,"mdd":mdd,"sharpe":sharpe,"trades":len(tr),"winrate":wr,"pf":pf,"avg":avg,"final":eq.Equity.iloc[-1]}

def pct(x): return "N/A" if x is None or not np.isfinite(x) else f"{x*100:,.2f}%"

st.title("📈 APEX AI 주식매매 봇 v3")
st.caption("3개 모델 앙상블 · 시장 국면 반영 · 시간순 검증 · 다음 봉 진입")
st.warning("연구·모의투자용입니다. 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")
with st.sidebar:
    ticker=st.text_input("종목코드","005930.KS").strip().upper(); interval=st.selectbox("봉 간격",["1d","1h","30m","15m"])
    periods={"1d":["2y","5y","10y","max"],"1h":["3mo","6mo","1y","2y"],"30m":["3mo","6mo"],"15m":["3mo","6mo"]}; period=st.selectbox("기간",periods[interval],index=min(1,len(periods[interval])-1))
    train_ratio=st.slider("학습 비율",.60,.85,.70,.05); future=st.slider("미래 봉 수",1,10,3); target=st.number_input("상승 기준(%)",-.5,5.,.2,.1); signal_rate=st.slider("목표 신호 비율",.05,.30,.15,.01)
    initial=st.number_input("초기자금",100000,1000000000,10000000,100000); risk=st.slider("1회 허용손실(%)",.1,2.,.5,.1); stop=st.slider("손절 ATR",.5,3.,1.5,.1); take=st.slider("익절 ATR",1.,6.,3.,.1); maxbars=st.slider("최대 보유 봉",2,60,20); fee=st.number_input("편도 비용(%)",0.,1.,.10,.01); slip=st.number_input("슬리피지(%)",0.,1.,.05,.01)
    run=st.button("🚀 v3 검증 실행",type="primary")
if not run: st.info("왼쪽 위 메뉴에서 설정 후 실행하세요."); st.stop()
try:
    with st.spinner("시장 데이터·앙상블 학습·시간순 검증 중..."):
        raw=download_one(ticker,period,interval); market=download_one(benchmark_for(ticker),period,interval); data=make_features(raw,market,future,target/100); cut=int(len(data)*train_ratio); train=data.iloc[:cut].copy(); test=data.iloc[cut:].copy()
        if len(train)<350 or len(test)<100: raise ValueError("검증 데이터가 부족합니다. 기간을 늘리세요.")
        aucs,weights=cv_weights(train); cv_auc=float(np.average(aucs,weights=weights)); train_probs,_=fit_predict(train,train,weights); threshold=choose_threshold(train_probs,signal_rate); test["probability"],fitted=fit_predict(train,test,weights); test_auc=roc_auc_score(test.target,test.probability) if test.target.nunique()>1 else np.nan
        gate=cv_auc>=.53
        if gate: eq,tr,m=backtest(test,float(initial),fee/100,slip/100,risk/100,threshold,stop,take,maxbars)
        else:
            eq=pd.DataFrame({"Equity":np.full(len(test),float(initial))},index=test.index); tr=pd.DataFrame(); m={"return":0.,"buyhold":test.Close.iloc[-1]/test.Open.iloc[0]-1,"excess":-(test.Close.iloc[-1]/test.Open.iloc[0]-1),"mdd":0.,"sharpe":0.,"trades":0,"winrate":np.nan,"pf":np.nan,"avg":np.nan,"final":float(initial)}
    st.success(f"완료 · 학습 {len(train):,} / 검증 {len(test):,} / 임계값 {threshold:.3f}")
    st.write(f"모델별 CV AUC: RF {aucs[0]:.3f} · HGB {aucs[1]:.3f} · LR {aucs[2]:.3f}")
    a,b,c=st.columns(3); a.metric("앙상블 CV AUC",f"{cv_auc:.3f}"); b.metric("검증 AUC",f"{test_auc:.3f}"); c.metric("AI 통과 여부","통과" if gate else "거부")
    a,b,c,d=st.columns(4); a.metric("전략 수익률",pct(m['return'])); b.metric("매수보유",pct(m['buyhold'])); c.metric("초과수익",pct(m['excess'])); d.metric("최대낙폭",pct(m['mdd']))
    a,b,c,d=st.columns(4); a.metric("거래 수",f"{m['trades']}회"); b.metric("승률",pct(m['winrate']) if m['trades']>=5 else "표본 부족"); c.metric("Profit Factor",f"{m['pf']:.2f}" if m['trades']>=5 and np.isfinite(m['pf']) else "표본 부족"); d.metric("샤프",f"{m['sharpe']:.2f}")
    if not gate: st.error("학습 구간 시간순 CV AUC가 0.53 미만이라 매매를 자동 차단했습니다. 약한 AI로 돈을 잃지 않게 만든 정상 동작입니다.")
    elif not np.isfinite(test_auc) or test_auc<.53: st.error("학습에서는 통과했지만 검증구간에서 성능이 무너졌습니다. 실거래 금지입니다.")
    elif m['trades']<20: st.warning("거래가 20회 미만이라 결론을 내리기 어렵습니다.")
    else: st.info("통계 기준을 통과해도 최소 8주 모의투자가 필요합니다.")
    chart=pd.DataFrame({"전략":eq.Equity/float(initial)*100,"매수보유":test.Close/test.Open.iloc[0]*100}); st.line_chart(chart)
    st.subheader("거래내역")
    if tr.empty: st.write("거래 없음")
    else:
        show=tr.copy(); show["수익률"]=(show["수익률"]*100).round(2).astype(str)+"%"; st.dataframe(show,use_container_width=True,hide_index=True); st.download_button("CSV 다운로드",tr.to_csv(index=False).encode("utf-8-sig"),f"{ticker}_v3_trades.csv","text/csv")
except Exception as e: st.error(f"실행 오류: {e}")
