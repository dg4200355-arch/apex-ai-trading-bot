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

st.set_page_config(page_title="APEX AI 종목 스캐너 v4", page_icon="🔎", layout="wide")
st.markdown("""
<style>
.block-container{padding:1rem .8rem 2rem;max-width:1200px}
h1{font-size:clamp(1.45rem,6vw,2.25rem)!important}
.stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
[data-testid="stMetricValue"]{font-size:clamp(1.05rem,5vw,1.7rem)}
@media(max-width:768px){[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}[data-testid="stSidebar"]{min-width:90vw;max-width:90vw}}
</style>
""", unsafe_allow_html=True)

KOREA = {
    "삼성전자":"005930.KS","SK하이닉스":"000660.KS","현대차":"005380.KS",
    "기아":"000270.KS","NAVER":"035420.KS","카카오":"035720.KS",
    "삼성바이오로직스":"207940.KS","셀트리온":"068270.KS",
    "LG에너지솔루션":"373220.KS","POSCO홀딩스":"005490.KS",
    "한화에어로스페이스":"012450.KS","HD현대중공업":"329180.KS"
}
USA = {
    "Apple":"AAPL","Microsoft":"MSFT","NVIDIA":"NVDA","Amazon":"AMZN",
    "Meta":"META","Alphabet":"GOOGL","Tesla":"TSLA","Broadcom":"AVGO",
    "AMD":"AMD","Netflix":"NFLX","JPMorgan":"JPM","Eli Lilly":"LLY"
}
FEATURES = ["ret1","ret3","ret5","ret10","ema8_21","ema21_55","ema55_200","rsi","macd","hist","atr_pct","bb_pos","vol_ratio","volatility","range_pct","market_ret5","relative5"]

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

def ema(s,n): return s.ewm(span=n,adjust=False).mean()

def rsi(s,n=14):
    x=s.diff(); g=x.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); l=(-x.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
    return (100-100/(1+g/l.replace(0,np.nan))).fillna(50)

def atr(d,n=14):
    pc=d.Close.shift(1)
    tr=pd.concat([d.High-d.Low,(d.High-pc).abs(),(d.Low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False).mean()

def make_features(raw, market, future=5, target_pct=0.01):
    d=raw.copy()
    m=market.Close.pct_change().rename("market_ret1")
    d=d.join(m,how="left").ffill()
    for n in [8,21,55,200]: d[f"ema{n}"]=ema(d.Close,n)
    d["rsi"]=rsi(d.Close)
    macd=ema(d.Close,12)-ema(d.Close,26); sig=ema(macd,9)
    d["macd"]=macd/d.Close; d["hist"]=(macd-sig)/d.Close
    d["atr"]=atr(d); d["atr_pct"]=d.atr/d.Close
    mid=d.Close.rolling(20).mean(); sd=d.Close.rolling(20).std(); lo=mid-2*sd; hi=mid+2*sd
    d["bb_pos"]=(d.Close-lo)/(hi-lo).replace(0,np.nan)
    d["vol_ratio"]=d.Volume/d.Volume.rolling(20).mean()
    d["volatility"]=d.Close.pct_change().rolling(10).std()
    d["range_pct"]=(d.High-d.Low)/d.Close
    for n in [1,3,5,10]: d[f"ret{n}"]=d.Close.pct_change(n)
    d["ema8_21"]=d.ema8/d.ema21-1; d["ema21_55"]=d.ema21/d.ema55-1; d["ema55_200"]=d.ema55/d.ema200-1
    d["market_ret5"]=(1+d.market_ret1).rolling(5).apply(np.prod,raw=True)-1
    d["relative5"]=d.ret5-d.market_ret5
    d["future_return"]=d.Close.shift(-future)/d.Close-1
    d["target"]=(d.future_return>target_pct).astype(int)
    return d.replace([np.inf,-np.inf],np.nan).dropna()

def models():
    return {
        "LR":Pipeline([("scale",StandardScaler()),("model",LogisticRegression(max_iter=1000,class_weight="balanced",C=.35))]),
        "HGB":HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=12,learning_rate=.05,l2_regularization=1.5,random_state=42)
    }

def cv_probabilities(train):
    splitter=TimeSeriesSplit(n_splits=3)
    scores={"LR":[],"HGB":[]}
    for tr_idx,va_idx in splitter.split(train):
        tr,va=train.iloc[tr_idx],train.iloc[va_idx]
        if tr.target.nunique()<2 or va.target.nunique()<2: continue
        for name,model in models().items():
            model.fit(tr[FEATURES],tr.target)
            p=model.predict_proba(va[FEATURES])[:,1]
            scores[name].append(roc_auc_score(va.target,p))
    return {k:(float(np.mean(v)) if v else np.nan) for k,v in scores.items()}

def simple_backtest(test, probs, threshold, fee=.0015):
    signal=(pd.Series(probs,index=test.index).shift(1)>=threshold) & (test.Close.shift(1)>test.ema55.shift(1)) & (test.ema21.shift(1)>test.ema55.shift(1))
    forward=test.Close.pct_change().fillna(0)
    strategy=signal.shift(1).fillna(False).astype(float)*forward
    changes=signal.astype(int).diff().abs().fillna(0)
    strategy=strategy-changes*fee
    equity=(1+strategy).cumprod()
    total=float(equity.iloc[-1]-1)
    mdd=float((equity/equity.cummax()-1).min())
    trades=int(((signal.astype(int).diff()==1)).sum())
    wins=[]
    in_trade=False; start=1.0
    for i,s in enumerate(signal):
        if s and not in_trade: in_trade=True; start=float(test.Close.iloc[i])
        if in_trade and (not s or i==len(signal)-1):
            end=float(test.Close.iloc[i]); wins.append(end/start-1-2*fee); in_trade=False
    wr=float(np.mean(np.array(wins)>0)) if wins else np.nan
    pf=np.nan
    if wins:
        pos=sum(x for x in wins if x>0); neg=abs(sum(x for x in wins if x<=0)); pf=pos/neg if neg>0 else np.nan
    return total,mdd,trades,wr,pf

def analyze(name,ticker,market,period,future,target_pct,min_cv,min_holdout):
    raw=download_one(ticker,period)
    data=make_features(raw,market,future,target_pct)
    if len(data)<600: raise ValueError("데이터 부족")
    cut=int(len(data)*.72); train=data.iloc[:cut].copy(); test=data.iloc[cut:].copy()
    if train.target.nunique()<2 or test.target.nunique()<2: raise ValueError("분류 데이터 부족")
    cvs=cv_probabilities(train)
    fitted={}; test_probs=[]; weights=[]
    for model_name,model in models().items():
        model.fit(train[FEATURES],train.target); fitted[model_name]=model
        p=model.predict_proba(test[FEATURES])[:,1]
        w=max(.01,(cvs.get(model_name,np.nan) if np.isfinite(cvs.get(model_name,np.nan)) else .5)-.45)
        test_probs.append(p); weights.append(w)
    ensemble=np.average(np.vstack(test_probs),axis=0,weights=weights)
    holdout=roc_auc_score(test.target,ensemble)
    cv_auc=float(np.average([cvs["LR"],cvs["HGB"]],weights=weights))
    threshold=float(np.quantile(ensemble,.75))
    total,mdd,trades,wr,pf=simple_backtest(test,ensemble,threshold)
    buyhold=float(test.Close.iloc[-1]/test.Close.iloc[0]-1)
    passed=(cv_auc>=min_cv and holdout>=min_holdout and trades>=5 and mdd>=-.15 and (np.isnan(pf) or pf>=1.0))
    score=(cv_auc-.5)*120+(holdout-.5)*100+total*25+mdd*10+min(trades,20)*.15
    return {"종목":name,"코드":ticker,"CV AUC":cv_auc,"검증 AUC":holdout,"전략 수익률":total,"매수보유":buyhold,"MDD":mdd,"거래수":trades,"승률":wr,"PF":pf,"통과":"✅" if passed else "❌","점수":score}

def pct(x): return "-" if not np.isfinite(x) else f"{x*100:.2f}%"

st.title("🔎 APEX AI 종목 스캐너 v4")
st.caption("여러 종목을 자동 검증해 AI 성능과 백테스트 기준을 통과한 후보만 정렬합니다.")
st.warning("연구·모의투자용입니다. 통과 종목도 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")

with st.sidebar:
    st.header("스캔 설정")
    market_choice=st.selectbox("시장",["한국 주요 종목","미국 주요 종목","직접 입력"])
    period=st.selectbox("데이터 기간",["5y","10y"],index=0)
    max_count=st.slider("검사 종목 수",3,12,8)
    future=st.slider("예측 기간(거래일)",2,10,5)
    target_pct=st.slider("상승 판정 기준(%)",0.0,5.0,1.0,.1)/100
    min_cv=st.slider("최소 CV AUC",.50,.65,.53,.01)
    min_holdout=st.slider("최소 검증 AUC",.50,.65,.53,.01)
    custom=st.text_area("직접 입력 코드(쉼표 구분)","005930.KS,000660.KS,NVDA,AAPL")
    run=st.button("🚀 전체 자동 스캔",type="primary")

if not run:
    st.info("왼쪽 메뉴에서 시장과 종목 수를 고른 뒤 전체 자동 스캔을 누르세요.")
    st.stop()

if market_choice=="한국 주요 종목":
    universe=list(KOREA.items())[:max_count]; benchmark="^KS11"
elif market_choice=="미국 주요 종목":
    universe=list(USA.items())[:max_count]; benchmark="SPY"
else:
    codes=[x.strip().upper() for x in custom.split(",") if x.strip()][:max_count]
    universe=[(x,x) for x in codes]; benchmark="^KS11" if any(x.endswith((".KS",".KQ")) for x in codes) else "SPY"

progress=st.progress(0,text="시장 데이터 준비 중...")
rows=[]; errors=[]
try:
    market=download_one(benchmark,period)
    for i,(name,ticker) in enumerate(universe):
        progress.progress(i/len(universe),text=f"{i+1}/{len(universe)} {name} 검사 중")
        try: rows.append(analyze(name,ticker,market,period,future,target_pct,min_cv,min_holdout))
        except Exception as e: errors.append(f"{name}: {e}")
    progress.progress(1.0,text="스캔 완료")
except Exception as e:
    st.error(f"시장 데이터 오류: {e}"); st.stop()

if not rows:
    st.error("분석 가능한 종목이 없습니다.")
    if errors: st.code("\n".join(errors))
    st.stop()

result=pd.DataFrame(rows).sort_values(["통과","점수"],ascending=[True,False]).reset_index(drop=True)
passed=result[result["통과"]=="✅"]

c1,c2,c3,c4=st.columns(4)
c1.metric("검사 종목",f"{len(result)}개")
c2.metric("통과 종목",f"{len(passed)}개")
c3.metric("최고 CV AUC",f"{result['CV AUC'].max():.3f}")
c4.metric("최고 검증 AUC",f"{result['검증 AUC'].max():.3f}")

if len(passed): st.success("통과 후보가 있습니다. 그래도 모의투자와 추가 기간 검증이 필요합니다.")
else: st.error("현재 기준을 모두 통과한 종목이 없습니다. 억지 매매보다 관망이 맞습니다.")

show=result.copy()
for col in ["전략 수익률","매수보유","MDD","승률"]: show[col]=show[col].apply(pct)
for col in ["CV AUC","검증 AUC","PF","점수"]: show[col]=show[col].apply(lambda x:"-" if not np.isfinite(x) else f"{x:.3f}")
st.dataframe(show[["통과","종목","코드","CV AUC","검증 AUC","전략 수익률","매수보유","MDD","거래수","승률","PF","점수"]],use_container_width=True,hide_index=True)

st.subheader("종목별 AI 성능")
st.bar_chart(result.set_index("종목")[["CV AUC","검증 AUC"]])

st.download_button("스캔 결과 CSV 다운로드",result.to_csv(index=False).encode("utf-8-sig"),"apex_scanner_results.csv","text/csv")
if errors:
    with st.expander("분석 제외 종목"):
        st.code("\n".join(errors))
