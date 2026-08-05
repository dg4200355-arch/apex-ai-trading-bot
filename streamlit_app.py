import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="APEX AI 종목 스캐너 v6", page_icon="🔎", layout="wide")
st.markdown("""
<style>
.block-container{padding:1rem .8rem 2rem;max-width:1250px}
h1{font-size:clamp(1.45rem,6vw,2.25rem)!important}
.stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
[data-testid="stMetricValue"]{font-size:clamp(1.05rem,5vw,1.7rem)}
@media(max-width:768px){[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}[data-testid="stSidebar"]{min-width:90vw;max-width:90vw}}
</style>
""", unsafe_allow_html=True)

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

FEATURES = [
    "ret1","ret3","ret5","ret10","ema8_21","ema21_55","ema55_200","rsi","macd","hist",
    "atr_pct","bb_pos","vol_ratio","volatility","range_pct","market_ret5","relative5"
]

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

def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rsi(s, n=14):
    x = s.diff()
    gain = x.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    loss = (-x.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return (100 - 100/(1 + gain/loss.replace(0, np.nan))).fillna(50)

def atr(d, n=14):
    pc = d.Close.shift(1)
    tr = pd.concat([d.High-d.Low, (d.High-pc).abs(), (d.Low-pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()

def make_features(raw, market, future=5, target_pct=.01):
    d = raw.copy()
    m = market.Close.pct_change().rename("market_ret1")
    d = d.join(m, how="left").ffill()
    for n in [8,21,55,200]:
        d[f"ema{n}"] = ema(d.Close, n)
    d["rsi"] = rsi(d.Close)
    macd = ema(d.Close,12)-ema(d.Close,26)
    sig = ema(macd,9)
    d["macd"] = macd/d.Close
    d["hist"] = (macd-sig)/d.Close
    d["atr"] = atr(d)
    d["atr_pct"] = d.atr/d.Close
    mid = d.Close.rolling(20).mean()
    sd = d.Close.rolling(20).std()
    lo, hi = mid-2*sd, mid+2*sd
    d["bb_pos"] = (d.Close-lo)/(hi-lo).replace(0,np.nan)
    d["vol_ratio"] = d.Volume/d.Volume.rolling(20).mean()
    d["volatility"] = d.Close.pct_change().rolling(10).std()
    d["range_pct"] = (d.High-d.Low)/d.Close
    for n in [1,3,5,10]:
        d[f"ret{n}"] = d.Close.pct_change(n)
    d["ema8_21"] = d.ema8/d.ema21-1
    d["ema21_55"] = d.ema21/d.ema55-1
    d["ema55_200"] = d.ema55/d.ema200-1
    d["market_ret5"] = (1+d.market_ret1).rolling(5).apply(np.prod, raw=True)-1
    d["relative5"] = d.ret5-d.market_ret5
    d["future_return"] = d.Close.shift(-future)/d.Close-1
    d["target"] = (d.future_return>target_pct).astype(int)
    return d.replace([np.inf,-np.inf],np.nan).dropna()

def build_models(fast_mode):
    hgb_iter = 90 if fast_mode else 150
    folds = 3 if fast_mode else 4
    return {
        "models": {
            "LR": Pipeline([("scale",StandardScaler()),("model",LogisticRegression(max_iter=700,class_weight="balanced",C=.35))]),
            "HGB": HistGradientBoostingClassifier(max_iter=hgb_iter,max_leaf_nodes=12,learning_rate=.05,l2_regularization=1.5,random_state=42)
        },
        "folds": folds
    }

def cv_scores(train, fast_mode):
    cfg = build_models(fast_mode)
    splitter = TimeSeriesSplit(n_splits=cfg["folds"])
    scores = {"LR":[],"HGB":[]}
    for tr_idx, va_idx in splitter.split(train):
        tr, va = train.iloc[tr_idx], train.iloc[va_idx]
        if tr.target.nunique()<2 or va.target.nunique()<2:
            continue
        for name, model in cfg["models"].items():
            model.fit(tr[FEATURES], tr.target)
            p = model.predict_proba(va[FEATURES])[:,1]
            scores[name].append(roc_auc_score(va.target,p))
    return {k:(float(np.mean(v)) if v else np.nan) for k,v in scores.items()}

def fit_ensemble(train, test, cvs, fast_mode):
    probs, weights = [], []
    for name, model in build_models(fast_mode)["models"].items():
        model.fit(train[FEATURES], train.target)
        probs.append(model.predict_proba(test[FEATURES])[:,1])
        score = cvs.get(name,np.nan)
        weights.append(max(.01,(score if np.isfinite(score) else .5)-.45))
    ensemble = np.average(np.vstack(probs),axis=0,weights=weights)
    cv_auc = float(np.average([cvs["LR"],cvs["HGB"]],weights=weights))
    return ensemble, cv_auc

def backtest(test, probs, threshold, fee=.0015):
    p = pd.Series(probs,index=test.index)
    signal = (p.shift(1)>=threshold)&(test.Close.shift(1)>test.ema55.shift(1))&(test.ema21.shift(1)>test.ema55.shift(1))
    daily = test.Close.pct_change().fillna(0)
    changes = signal.astype(int).diff().abs().fillna(0)
    strat = signal.shift(1).fillna(False).astype(float)*daily-changes*fee
    equity = (1+strat).cumprod()
    total = float(equity.iloc[-1]-1)
    mdd = float((equity/equity.cummax()-1).min())
    trades = int((signal.astype(int).diff().fillna(0)==1).sum())
    trade_returns=[]; active=False; start=0.0
    for i,s in enumerate(signal):
        if s and not active:
            active=True; start=float(test.Close.iloc[i])
        if active and ((not s) or i==len(signal)-1):
            trade_returns.append(float(test.Close.iloc[i])/start-1-2*fee); active=False
    wr = float(np.mean(np.array(trade_returns)>0)) if trade_returns else np.nan
    pf = np.nan
    if trade_returns:
        pos=sum(x for x in trade_returns if x>0); neg=abs(sum(x for x in trade_returns if x<=0))
        pf=pos/neg if neg>0 else np.nan
    return total,mdd,trades,wr,pf

def analyze(name,ticker,market,period,future,target_pct,min_cv,min_holdout,min_trades,min_pf,max_mdd,fast_mode):
    raw=download_one(ticker,period)
    data=make_features(raw,market,future,target_pct)
    if len(data)<700:
        raise ValueError("데이터 부족")
    cut=int(len(data)*.70)
    train=data.iloc[:cut].copy(); test=data.iloc[cut:].copy()
    if train.target.nunique()<2 or test.target.nunique()<2:
        raise ValueError("분류 데이터 부족")
    cvs=cv_scores(train,fast_mode)
    probs,cv_auc=fit_ensemble(train,test,cvs,fast_mode)
    holdout=roc_auc_score(test.target,probs)
    threshold=float(np.quantile(probs,.75))
    total,mdd,trades,wr,pf=backtest(test,probs,threshold)
    recent_n=max(80,int(len(test)*.35))
    recent=test.iloc[-recent_n:].copy(); recent_probs=probs[-recent_n:]
    recent_total,recent_mdd,recent_trades,_,_=backtest(recent,recent_probs,float(np.quantile(recent_probs,.75)))
    buyhold=float(test.Close.iloc[-1]/test.Close.iloc[0]-1)
    pf_ok=np.isfinite(pf) and pf>=min_pf
    recent_ok=recent_total>0 and recent_trades>=3 and recent_mdd>=max_mdd
    passed=(cv_auc>=min_cv and holdout>=min_holdout and total>0 and trades>=min_trades and pf_ok and mdd>=max_mdd and recent_ok)
    reasons=[]
    if cv_auc<min_cv: reasons.append("CV AUC")
    if holdout<min_holdout: reasons.append("검증 AUC")
    if total<=0: reasons.append("수익률")
    if trades<min_trades: reasons.append("거래수")
    if not pf_ok: reasons.append("PF")
    if mdd<max_mdd: reasons.append("MDD")
    if not recent_ok: reasons.append("최근구간")
    score=(cv_auc-.5)*120+(holdout-.5)*100+total*25+mdd*10+recent_total*20+min(trades,30)*.1
    return {"통과":"✅" if passed else "❌","종목":name,"코드":ticker,"CV AUC":cv_auc,"검증 AUC":holdout,"전략 수익률":total,"최근 수익률":recent_total,"매수보유":buyhold,"MDD":mdd,"최근 MDD":recent_mdd,"거래수":trades,"최근 거래수":recent_trades,"승률":wr,"PF":pf,"탈락 사유":"-" if passed else ", ".join(reasons),"점수":score}

def pct(x):
    return "-" if not np.isfinite(x) else f"{x*100:.2f}%"

st.title("🔎 APEX AI 종목 스캐너 v6")
st.caption("한국·미국 최대 40종목 · 엄격 통과 기준 · 최근 구간 재검증")
st.warning("연구·모의투자용입니다. 통과 종목도 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")

with st.sidebar:
    st.header("스캔 범위")
    market_choice=st.selectbox("시장",["한국 40종목","미국 40종목","직접 입력"])
    period=st.selectbox("데이터 기간",["5y","10y"],index=0)
    max_count=st.slider("검사 종목 수",8,40,20,4)
    fast_mode=st.toggle("무료 서버 빠른 모드",value=True,help="모델 반복과 교차검증 횟수를 줄여 서버 중단 위험을 낮춥니다.")
    future=st.slider("예측 기간(거래일)",2,10,5)
    target_pct=st.slider("상승 판정 기준(%)",0.0,5.0,1.0,.1)/100
    st.header("엄격 통과 기준")
    min_cv=st.slider("최소 CV AUC",.50,.65,.53,.01)
    min_holdout=st.slider("최소 검증 AUC",.50,.65,.55,.01)
    min_trades=st.slider("최소 거래 수",5,40,15)
    min_pf=st.slider("최소 Profit Factor",1.0,2.5,1.3,.1)
    max_mdd=-st.slider("허용 최대낙폭(%)",5,30,15)/100
    custom=st.text_area("직접 입력 코드(쉼표 구분)","005930.KS,000660.KS,NVDA,AAPL")
    run=st.button("🚀 대규모 자동 스캔",type="primary")

if not run:
    st.info("처음에는 빠른 모드로 20개를 검사하고, 이후 32개·40개로 늘리세요.")
    st.stop()

if market_choice=="한국 40종목":
    universe=list(KOREA.items())[:max_count]; benchmark="^KS11"
elif market_choice=="미국 40종목":
    universe=list(USA.items())[:max_count]; benchmark="SPY"
else:
    codes=[x.strip().upper() for x in custom.split(",") if x.strip()][:max_count]
    universe=[(x,x) for x in codes]
    benchmark="^KS11" if any(x.endswith((".KS",".KQ")) for x in codes) else "SPY"

progress=st.progress(0,text="시장 데이터 준비 중...")
rows=[]; errors=[]
try:
    market=download_one(benchmark,period)
    for i,(name,ticker) in enumerate(universe):
        progress.progress(i/len(universe),text=f"{i+1}/{len(universe)} {name} 검사 중")
        try:
            rows.append(analyze(name,ticker,market,period,future,target_pct,min_cv,min_holdout,min_trades,min_pf,max_mdd,fast_mode))
        except Exception as e:
            errors.append(f"{name}: {e}")
    progress.progress(1.0,text="스캔 완료")
except Exception as e:
    st.error(f"시장 데이터 오류: {e}")
    st.stop()

if not rows:
    st.error("분석 가능한 종목이 없습니다.")
    if errors: st.code("\n".join(errors))
    st.stop()

result=pd.DataFrame(rows).sort_values(["통과","점수"],ascending=[True,False]).reset_index(drop=True)
passed=result[result["통과"]=="✅"]
cols=st.columns(4)
cols[0].metric("검사 완료",f"{len(result)}개")
cols[1].metric("엄격 통과",f"{len(passed)}개")
cols[2].metric("최고 CV AUC",f"{result['CV AUC'].max():.3f}")
cols[3].metric("최고 검증 AUC",f"{result['검증 AUC'].max():.3f}")

if len(passed):
    st.success("엄격 기준 통과 후보가 있습니다. 실거래 전 별도 모의투자 검증이 필요합니다.")
else:
    st.error("엄격 기준을 모두 통과한 종목이 없습니다. 현재는 관망이 맞습니다.")

show=result.copy()
for col in ["전략 수익률","최근 수익률","매수보유","MDD","최근 MDD","승률"]:
    show[col]=show[col].apply(pct)
for col in ["CV AUC","검증 AUC","PF","점수"]:
    show[col]=show[col].apply(lambda x:"-" if not np.isfinite(x) else f"{x:.3f}")
st.dataframe(show[["통과","종목","코드","CV AUC","검증 AUC","전략 수익률","최근 수익률","MDD","거래수","최근 거래수","승률","PF","탈락 사유","점수"]],use_container_width=True,hide_index=True)

st.subheader("종목별 AI 성능")
st.bar_chart(result.set_index("종목")[["CV AUC","검증 AUC"]])
st.download_button("스캔 결과 CSV 다운로드",result.to_csv(index=False).encode("utf-8-sig"),"apex_scanner_v6_results.csv","text/csv")

if errors:
    with st.expander(f"분석 제외 종목 {len(errors)}개"):
        st.code("\n".join(errors))
