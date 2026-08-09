import warnings
warnings.filterwarnings("ignore")

from dataclasses import dataclass
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

st.set_page_config(page_title="APEX Multi-Strategy Lab v7", page_icon="🧠", layout="wide")
st.markdown("""
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

@dataclass
class Perf:
    ret: float
    mdd: float
    trades: int
    winrate: float
    pf: float
    sharpe: float

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

def ema(s,n):
    return s.ewm(span=n, adjust=False).mean()

def rsi(s,n=14):
    x=s.diff()
    gain=x.clip(lower=0).ewm(alpha=1/n,adjust=False).mean()
    loss=(-x.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
    return (100-100/(1+gain/loss.replace(0,np.nan))).fillna(50)

def atr(d,n=14):
    pc=d.Close.shift(1)
    tr=pd.concat([d.High-d.Low,(d.High-pc).abs(),(d.Low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False).mean()

def make_features(raw, market, future=5, target_pct=.01):
    d=raw.copy()
    m=market.Close.pct_change().rename("market_ret1")
    d=d.join(m,how="left").ffill()
    for n in [8,20,21,55,100,200]:
        d[f"ema{n}"]=ema(d.Close,n)
    d["rsi"]=rsi(d.Close)
    macd=ema(d.Close,12)-ema(d.Close,26)
    sig=ema(macd,9)
    d["macd"]=macd/d.Close
    d["hist"]=(macd-sig)/d.Close
    d["atr"]=atr(d)
    d["atr_pct"]=d.atr/d.Close
    mid=d.Close.rolling(20).mean()
    sd=d.Close.rolling(20).std()
    lo,hi=mid-2*sd,mid+2*sd
    d["bb_pos"]=(d.Close-lo)/(hi-lo).replace(0,np.nan)
    d["vol_ratio"]=d.Volume/d.Volume.rolling(20).mean()
    d["volatility"]=d.Close.pct_change().rolling(10).std()
    d["range_pct"]=(d.High-d.Low)/d.Close
    for n in [1,3,5,10]:
        d[f"ret{n}"]=d.Close.pct_change(n)
    d["ema8_21"]=d.ema8/d.ema21-1
    d["ema21_55"]=d.ema21/d.ema55-1
    d["ema55_200"]=d.ema55/d.ema200-1
    d["market_ret5"]=(1+d.market_ret1).rolling(5).apply(np.prod,raw=True)-1
    d["relative5"]=d.ret5-d.market_ret5
    d["donchian20"]=d.High.rolling(20).max().shift(1)
    d["donchian55"]=d.High.rolling(55).max().shift(1)
    d["future_return"]=d.Close.shift(-future)/d.Close-1
    d["target"]=(d.future_return>target_pct).astype(int)
    return d.replace([np.inf,-np.inf],np.nan).dropna()

def perf_from_signal(d, raw_signal, fee=.0015):
    sig=pd.Series(raw_signal,index=d.index).fillna(False).astype(bool)
    pos=sig.shift(1).fillna(False).astype(float)
    daily=d.Close.pct_change().fillna(0.0)
    turns=pos.diff().abs().fillna(pos.abs())
    strat=pos*daily-turns*fee
    equity=(1+strat).cumprod()
    total=float(equity.iloc[-1]-1)
    mdd=float((equity/equity.cummax()-1).min())
    r=strat.dropna()
    sharpe=float(np.sqrt(252)*r.mean()/r.std()) if len(r)>5 and r.std()>0 else 0.0
    entries=(pos.diff().fillna(pos)==1)
    exits=(pos.diff().fillna(0)==-1)
    trade_returns=[]
    start_idx=None
    for i in range(len(d)):
        if entries.iloc[i] and start_idx is None:
            start_idx=i
        if start_idx is not None and (exits.iloc[i] or i==len(d)-1):
            seg=strat.iloc[start_idx:i+1]
            trade_returns.append(float((1+seg).prod()-1))
            start_idx=None
    trades=len(trade_returns)
    winrate=float(np.mean(np.array(trade_returns)>0)) if trades else np.nan
    pf=np.nan
    if trades:
        pos_sum=sum(x for x in trade_returns if x>0)
        neg_sum=abs(sum(x for x in trade_returns if x<=0))
        if neg_sum>0:
            pf=float(pos_sum/neg_sum)
    return Perf(total,mdd,trades,winrate,pf,sharpe)

def robust_score(p:Perf):
    if p.trades < 3 or p.mdd < -0.35:
        return -999.0
    pf = p.pf if np.isfinite(p.pf) else 1.0
    wr = p.winrate if np.isfinite(p.winrate) else 0.0
    return p.ret*2.8 + p.sharpe*0.12 + min(pf,3)*0.05 + wr*0.10 + p.mdd*0.55 + min(p.trades,30)*0.004

def stateful_mean_reversion(d, buy_bb, buy_rsi, exit_bb=.55, exit_rsi=55):
    out=[]
    active=False
    for _,r in d.iterrows():
        if not active and r.bb_pos<=buy_bb and r.rsi<=buy_rsi and r.Close>r.ema200*0.85:
            active=True
        elif active and (r.bb_pos>=exit_bb or r.rsi>=exit_rsi or r.Close<r.ema200*0.78):
            active=False
        out.append(active)
    return pd.Series(out,index=d.index)

def stateful_breakout(d, lookback=20, vol_min=1.0):
    level=d["donchian20"] if lookback==20 else d["donchian55"]
    out=[]
    active=False
    for i,(_,r) in enumerate(d.iterrows()):
        lv=float(level.iloc[i]) if pd.notna(level.iloc[i]) else np.nan
        if not active and np.isfinite(lv) and r.Close>lv and r.vol_ratio>=vol_min and r.Close>r.ema55:
            active=True
        elif active and (r.Close<r.ema20 or r.rsi<45):
            active=False
        out.append(active)
    return pd.Series(out,index=d.index)

def rule_candidates(d):
    cands=[]
    for fast,slow,ceil in [(8,55,78),(21,100,76),(21,200,74)]:
        sf=d[f"ema{fast}"] if f"ema{fast}" in d.columns else ema(d.Close,fast)
        ss=d[f"ema{slow}"] if f"ema{slow}" in d.columns else ema(d.Close,slow)
        sig=(d.Close>ss)&(sf>ss)&(d.rsi.between(48,ceil))&(d.vol_ratio>=.65)
        cands.append(("추세",{"fast":fast,"slow":slow,"rsi_max":ceil},sig))
    for buy_bb,buy_rsi in [(0.10,35),(0.18,38),(0.25,40)]:
        sig=stateful_mean_reversion(d,buy_bb,buy_rsi)
        cands.append(("반전",{"bb":buy_bb,"rsi":buy_rsi},sig))
    for lb,vol in [(20,.9),(20,1.15),(55,1.0)]:
        sig=stateful_breakout(d,lb,vol)
        cands.append(("돌파",{"lookback":lb,"vol":vol},sig))
    return cands

def ai_models(fast_mode=True):
    hgb_iter=80 if fast_mode else 140
    return {
        "LR":Pipeline([("scale",StandardScaler()),("model",LogisticRegression(max_iter=700,class_weight="balanced",C=.35))]),
        "HGB":HistGradientBoostingClassifier(max_iter=hgb_iter,max_leaf_nodes=12,learning_rate=.05,l2_regularization=1.5,random_state=42)
    }

def ai_cv_auc(train, fast_mode=True):
    splits=3 if fast_mode else 4
    tss=TimeSeriesSplit(n_splits=splits)
    scores={"LR":[],"HGB":[]}
    for tr_idx,va_idx in tss.split(train):
        tr=train.iloc[tr_idx]
        va=train.iloc[va_idx]
        if tr.target.nunique()<2 or va.target.nunique()<2:
            continue
        for name,m in ai_models(fast_mode).items():
            m.fit(tr[FEATURES],tr.target)
            p=m.predict_proba(va[FEATURES])[:,1]
            scores[name].append(roc_auc_score(va.target,p))
    vals=[]
    for k in ["LR","HGB"]:
        vals.append(float(np.mean(scores[k])) if scores[k] else np.nan)
    finite=[x for x in vals if np.isfinite(x)]
    return float(np.mean(finite)) if finite else np.nan

def ai_fit_predict(train, target, fast_mode=True):
    preds=[]
    for _,m in ai_models(fast_mode).items():
        m.fit(train[FEATURES],train.target)
        preds.append(m.predict_proba(target[FEATURES])[:,1])
    return np.mean(np.vstack(preds),axis=0)

def choose_rule_strategy(train, val, full, fee):
    choices=[]
    for kind,params,sig in rule_candidates(full):
        p_train=perf_from_signal(train,sig.reindex(train.index),fee)
        p_val=perf_from_signal(val,sig.reindex(val.index),fee)
        if robust_score(p_train)>-100 and p_train.ret>-0.08:
            choices.append((robust_score(p_val),kind,params,p_train,p_val))
    if not choices:
        return None
    choices.sort(key=lambda x:x[0],reverse=True)
    return choices[0]

def build_rule_signal(d, kind, params):
    if kind=="추세":
        sf=d[f"ema{params['fast']}"] if f"ema{params['fast']}" in d.columns else ema(d.Close,params["fast"])
        ss=d[f"ema{params['slow']}"] if f"ema{params['slow']}" in d.columns else ema(d.Close,params["slow"])
        return (d.Close>ss)&(sf>ss)&(d.rsi.between(48,params["rsi_max"]))&(d.vol_ratio>=.65)
    if kind=="반전":
        return stateful_mean_reversion(d,params["bb"],params["rsi"])
    return stateful_breakout(d,params["lookback"],params["vol"])

def analyze_stock(name,ticker,market,period,future,target_pct,fee,fast_mode):
    raw=download_one(ticker,period)
    data=make_features(raw,market,future,target_pct)
    if len(data)<850:
        raise ValueError("데이터 부족")
    n=len(data)
    a=int(n*.60)
    b=int(n*.80)
    train=data.iloc[:a].copy()
    val=data.iloc[a:b].copy()
    test=data.iloc[b:].copy()
    if min(len(train),len(val),len(test))<120:
        raise ValueError("검증 구간 부족")

    rule_pick=choose_rule_strategy(train,val,data,fee)
    cv_auc=ai_cv_auc(train,fast_mode)
    ai_candidate=None
    if train.target.nunique()>1 and val.target.nunique()>1:
        val_p=ai_fit_predict(train,val,fast_mode)
        best=None
        for th in [.52,.56,.60,.64]:
            sig=(pd.Series(val_p,index=val.index)>=th)&(val.Close>val.ema55)&(val.rsi.between(45,78))
            pv=perf_from_signal(val,sig,fee)
            s=robust_score(pv)
            if best is None or s>best[0]:
                best=(s,th,pv)
        ai_candidate=(best[0],"AI",{"threshold":best[1]},best[2])

    finalists=[]
    if rule_pick is not None:
        finalists.append((rule_pick[0],rule_pick[1],rule_pick[2],rule_pick[4]))
    if ai_candidate is not None and np.isfinite(cv_auc) and cv_auc>=.50:
        finalists.append(ai_candidate)
    if not finalists:
        raise ValueError("선택 가능한 전략 없음")
    finalists.sort(key=lambda x:x[0],reverse=True)
    _,strategy,params,val_perf=finalists[0]

    if strategy=="AI":
        train_val=data.iloc[:b].copy()
        test_p=ai_fit_predict(train_val,test,fast_mode)
        test_auc=roc_auc_score(test.target,test_p) if test.target.nunique()>1 else np.nan
        test_sig=(pd.Series(test_p,index=test.index)>=params["threshold"])&(test.Close>test.ema55)&(test.rsi.between(45,78))
        val_p=ai_fit_predict(train,val,fast_mode)
        val_sig=(pd.Series(val_p,index=val.index)>=params["threshold"])&(val.Close>val.ema55)&(val.rsi.between(45,78))
    else:
        test_auc=np.nan
        full_sig=build_rule_signal(data,strategy,params)
        test_sig=full_sig.reindex(test.index)
        val_sig=full_sig.reindex(val.index)

    test_perf=perf_from_signal(test,test_sig,fee)
    recent_n=min(60,len(test))
    recent=test.iloc[-recent_n:].copy()
    recent_perf=perf_from_signal(recent,test_sig.reindex(recent.index),fee)
    oos=pd.concat([val,test])
    oos_sig=pd.concat([val_sig,test_sig]).reindex(oos.index)
    oos_perf=perf_from_signal(oos,oos_sig,fee)
    buyhold=float(test.Close.iloc[-1]/test.Close.iloc[0]-1)

    reasons=[]
    if val_perf.ret<=0: reasons.append("검증수익")
    if test_perf.ret<=0: reasons.append("최종수익")
    if oos_perf.trades<8: reasons.append("거래수")
    if not np.isfinite(oos_perf.pf) or oos_perf.pf<1.20: reasons.append("PF")
    if test_perf.mdd<-0.15: reasons.append("MDD")
    if test_perf.sharpe<0.25: reasons.append("샤프")
    if recent_perf.ret<-0.03: reasons.append("최근구간")
    if strategy=="AI":
        if not np.isfinite(cv_auc) or cv_auc<.52: reasons.append("AI CV")
        if not np.isfinite(test_auc) or test_auc<.52: reasons.append("AI TEST")
    passed=len(reasons)==0

    score=(oos_perf.ret*35 + test_perf.ret*35 + val_perf.ret*15 +
           min(oos_perf.pf if np.isfinite(oos_perf.pf) else 0,3)*2 +
           test_perf.sharpe*3 + test_perf.mdd*10 + recent_perf.ret*10 + min(oos_perf.trades,30)*.08)
    return {
        "통과":"✅" if passed else "❌","종목":name,"코드":ticker,"선택전략":strategy,
        "검증수익":val_perf.ret,"최종수익":test_perf.ret,"OOS수익":oos_perf.ret,"최근60일":recent_perf.ret,
        "매수보유":buyhold,"MDD":test_perf.mdd,"거래수":oos_perf.trades,"승률":oos_perf.winrate,"PF":oos_perf.pf,
        "샤프":test_perf.sharpe,"AI CV AUC":cv_auc if strategy=="AI" else np.nan,
        "AI TEST AUC":test_auc if strategy=="AI" else np.nan,"탈락사유":"-" if passed else ", ".join(reasons),"점수":score
    }

def pct(x):
    return "-" if not np.isfinite(x) else f"{x*100:.2f}%"

def synthetic_sanity_check():
    idx=pd.date_range("2022-01-01",periods=320,freq="B")
    rng=np.random.default_rng(42)
    close=100*np.exp(np.cumsum(rng.normal(.0003,.012,len(idx))))
    d=pd.DataFrame(index=idx)
    d["Close"]=close
    d["Open"]=close*(1+rng.normal(0,.002,len(idx)))
    d["High"]=np.maximum(d.Open,d.Close)*(1+np.abs(rng.normal(0,.004,len(idx))))
    d["Low"]=np.minimum(d.Open,d.Close)*(1-np.abs(rng.normal(0,.004,len(idx))))
    d["Volume"]=rng.integers(100000,1000000,len(idx))
    d["ema20"]=ema(d.Close,20); d["ema55"]=ema(d.Close,55); d["rsi"]=rsi(d.Close)
    d["vol_ratio"]=d.Volume/d.Volume.rolling(20).mean()
    d["donchian20"]=d.High.rolling(20).max().shift(1)
    d["donchian55"]=d.High.rolling(55).max().shift(1)
    dd=d.dropna()
    sig=(dd.Close>dd.ema55)&(dd.rsi<78)
    p=perf_from_signal(dd,sig)
    return bool(np.isfinite(p.ret) and np.isfinite(p.mdd) and p.mdd<=0 and p.ret>-1)

st.title("🧠 APEX Multi-Strategy Lab v7")
st.caption("추세·반전·돌파·AI를 경쟁시킨 뒤 validation에서 1개만 선택하고, 마지막 test 구간은 끝까지 숨겨둔 채 최종 검증합니다.")
st.warning("연구·모의투자용입니다. 어떤 백테스트도 미래 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.")

if synthetic_sanity_check():
    st.success("내부 시뮬레이션 엔진 점검 통과 · 다음 봉 적용/수수료 반영/최종 test 분리")
else:
    st.error("내부 시뮬레이션 엔진 점검 실패")
    st.stop()

with st.sidebar:
    st.header("스캔 범위")
    market_choice=st.selectbox("시장",["한국 40종목","미국 40종목","직접 입력"])
    period=st.selectbox("데이터 기간",["5y","10y"],index=0)
    max_count=st.slider("검사 종목 수",4,30,12,2)
    fast_mode=st.toggle("무료 서버 빠른 모드",value=True)
    future=st.slider("AI 예측 기간(거래일)",2,10,5)
    target_pct=st.slider("AI 상승 판정 기준(%)",0.0,5.0,1.0,.1)/100
    fee=st.slider("편도 거래비용 가정(%)",0.05,0.30,0.15,.01)/100
    custom=st.text_area("직접 입력 코드(쉼표)", "005930.KS,000660.KS,NVDA,AAPL")
    run=st.button("🚀 최종 시뮬레이션 실행",type="primary")

if not run:
    st.info("왼쪽 메뉴에서 시장과 종목 수를 정한 뒤 최종 시뮬레이션 실행을 누르세요.")
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
        progress.progress(i/len(universe),text=f"{i+1}/{len(universe)} {name} · 다중전략 검증 중")
        try:
            rows.append(analyze_stock(name,ticker,market,period,future,target_pct,fee,fast_mode))
        except Exception as e:
            errors.append(f"{name}: {e}")
    progress.progress(1.0,text="최종 시뮬레이션 완료")
except Exception as e:
    st.error(f"시장 데이터 오류: {e}")
    st.stop()

if not rows:
    st.error("분석 가능한 종목이 없습니다.")
    if errors: st.code("\n".join(errors))
    st.stop()

result=pd.DataFrame(rows).sort_values(["통과","점수"],ascending=[True,False]).reset_index(drop=True)
passed=result[result["통과"]=="✅"]

c1,c2,c3,c4=st.columns(4)
c1.metric("검사",f"{len(result)}개")
c2.metric("최종 통과",f"{len(passed)}개")
c3.metric("최고 OOS",pct(result["OOS수익"].max()))
pf_max=result["PF"].replace([np.inf,-np.inf],np.nan).max()
c4.metric("최고 PF",f"{pf_max:.2f}" if np.isfinite(pf_max) else "-")

if len(passed):
    st.success("최종 test까지 통과한 모의투자 후보가 있습니다. 그래도 실제 자금 전에는 추가 모의검증이 필요합니다.")
else:
    st.error("최종 test까지 통과한 종목이 없습니다. 이 경우 앱의 답은 '관망'입니다.")

show=result.copy()
for col in ["검증수익","최종수익","OOS수익","최근60일","매수보유","MDD","승률"]:
    show[col]=show[col].apply(pct)
for col in ["PF","샤프","AI CV AUC","AI TEST AUC","점수"]:
    show[col]=show[col].apply(lambda x:"-" if not np.isfinite(x) else f"{x:.3f}")

cols=["통과","종목","코드","선택전략","검증수익","최종수익","OOS수익","최근60일","MDD","거래수","승률","PF","샤프","AI CV AUC","AI TEST AUC","탈락사유","점수"]
st.dataframe(show[cols],use_container_width=True,hide_index=True)

st.subheader("전략별 선택 분포")
st.bar_chart(result["선택전략"].value_counts())

st.subheader("상위 후보 OOS vs 최종 test")
chart=result.set_index("종목")[["OOS수익","최종수익"]].head(12)*100
st.bar_chart(chart)

st.download_button("최종 시뮬레이션 CSV",result.to_csv(index=False).encode("utf-8-sig"),"apex_v7_results.csv","text/csv")

if errors:
    with st.expander("분석 제외 종목"):
        st.code("\n".join(errors))
