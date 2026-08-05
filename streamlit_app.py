import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

st.set_page_config(page_title='APEX AI 주식매매 봇', page_icon='📈', layout='wide')
st.markdown('''
<style>
.block-container{padding:1rem .8rem 2rem;max-width:1200px}
h1{font-size:clamp(1.5rem,6vw,2.3rem)!important}
.stButton>button,.stDownloadButton>button{min-height:3rem;font-weight:700;width:100%}
[data-testid="stMetricValue"]{font-size:clamp(1.1rem,5vw,1.8rem)}
@media(max-width:768px){[data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}[data-testid="stSidebar"]{min-width:88vw;max-width:88vw}}
</style>
''', unsafe_allow_html=True)

FEATURES=['ret1','ret3','ret5','ema8_21','ema21_55','ema55_200','rsi','macd','hist','atr_pct','bb_pos','vol_ratio','volatility']

@st.cache_data(ttl=3600, show_spinner=False)
def load_data(ticker, period, interval):
    d=yf.download(ticker,period=period,interval=interval,auto_adjust=True,progress=False,threads=False)
    if d is None or d.empty: raise ValueError('가격 데이터를 받지 못했습니다. 종목코드를 확인하세요.')
    if isinstance(d.columns,pd.MultiIndex): d.columns=d.columns.get_level_values(0)
    d.columns=[str(c).title() for c in d.columns]
    need=['Open','High','Low','Close','Volume']
    if any(c not in d.columns for c in need): raise ValueError('가격 데이터 형식이 올바르지 않습니다.')
    d=d[need].dropna()
    if len(d)<300: raise ValueError(f'데이터가 {len(d)}개뿐입니다. 기간을 늘리거나 일봉을 선택하세요.')
    return d

def ema(s,n): return s.ewm(span=n,adjust=False).mean()

def rsi(s,n=14):
    x=s.diff(); g=x.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); l=(-x.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
    return (100-100/(1+g/l.replace(0,np.nan))).fillna(50)

def atr(d,n=14):
    pc=d.Close.shift(1)
    tr=pd.concat([d.High-d.Low,(d.High-pc).abs(),(d.Low-pc).abs()],axis=1).max(axis=1)
    return tr.ewm(alpha=1/n,adjust=False).mean()

def make_features(raw,future,target_pct):
    d=raw.copy()
    for n in [8,21,55,200]: d[f'ema{n}']=ema(d.Close,n)
    d['rsi']=rsi(d.Close); d['macd']=ema(d.Close,12)-ema(d.Close,26); d['signal']=ema(d.macd,9); d['hist']=d.macd-d.signal
    d['atr']=atr(d); d['atr_pct']=d.atr/d.Close
    mid=d.Close.rolling(20).mean(); sd=d.Close.rolling(20).std(); lo=mid-2*sd; hi=mid+2*sd
    d['bb_pos']=(d.Close-lo)/(hi-lo).replace(0,np.nan); d['vol_ratio']=d.Volume/d.Volume.rolling(20).mean(); d['volatility']=d.Close.pct_change().rolling(10).std()
    d['ret1']=d.Close.pct_change(); d['ret3']=d.Close.pct_change(3); d['ret5']=d.Close.pct_change(5)
    d['ema8_21']=d.ema8/d.ema21-1; d['ema21_55']=d.ema21/d.ema55-1; d['ema55_200']=d.ema55/d.ema200-1
    d['future_return']=d.Close.shift(-future)/d.Close-1; d['target']=(d.future_return>target_pct).astype(int)
    return d.replace([np.inf,-np.inf],np.nan).dropna()

def backtest(test,initial_cash,fee,slip,risk,threshold,stop_atr,take_atr,max_bars):
    cash=float(initial_cash); shares=0; entry=stop=take=0.; entry_i=None; trades=[]; curve=[]
    for i,(dt,row) in enumerate(test.iterrows()):
        c=float(row.Close); h=float(row.High); l=float(row.Low); a=float(row.atr); p=float(row.probability)
        if shares:
            reason=None; px=c
            if l<=stop: reason='ATR 손절'; px=stop*(1-slip)
            elif h>=take: reason='ATR 익절'; px=take*(1-slip)
            elif i-entry_i>=max_bars: reason='최대 보유기간'; px=c*(1-slip)
            elif p<.45 or c<float(row.ema21): reason='AI/추세 이탈'; px=c*(1-slip)
            if reason:
                gross=shares*px; exit_fee=gross*fee; cash+=gross-exit_fee; pnl=gross-exit_fee-shares*entry
                trades.append({'진입일':test.index[entry_i],'청산일':dt,'진입가':entry,'청산가':px,'수량':shares,'손익':pnl,'수익률':pnl/(shares*entry),'청산사유':reason}); shares=0
        if not shares:
            trend=c>row.ema200 and row.ema8>row.ema21>row.ema55 and 48<=row.rsi<=72 and row.vol_ratio>=.8
            if trend and p>=threshold and a>0:
                risk_cash=cash*risk; risk_share=stop_atr*a
                qty=min(int(risk_cash/risk_share),int(cash/(c*(1+fee+slip)))) if risk_share>0 else 0
                if qty>0:
                    entry=c*(1+slip); cost=qty*entry; buy_fee=cost*fee
                    if cost+buy_fee<=cash:
                        cash-=cost+buy_fee; shares=qty; entry_i=i; stop=entry-stop_atr*a; take=entry+take_atr*a
        curve.append({'Date':dt,'Equity':cash+shares*c})
    if shares:
        px=float(test.Close.iloc[-1])*(1-slip); gross=shares*px; exit_fee=gross*fee; cash+=gross-exit_fee; pnl=gross-exit_fee-shares*entry
        trades.append({'진입일':test.index[entry_i],'청산일':test.index[-1],'진입가':entry,'청산가':px,'수량':shares,'손익':pnl,'수익률':pnl/(shares*entry),'청산사유':'테스트 종료'}); curve[-1]['Equity']=cash
    eq=pd.DataFrame(curve).set_index('Date'); tr=pd.DataFrame(trades)
    total=eq.Equity.iloc[-1]/initial_cash-1; mdd=(eq.Equity/eq.Equity.cummax()-1).min(); rr=eq.Equity.pct_change().dropna(); sharpe=np.sqrt(252)*rr.mean()/rr.std() if len(rr)>2 and rr.std()>0 else 0
    if len(tr):
        wins=tr[tr.손익>0]; losses=tr[tr.손익<=0]; wr=len(wins)/len(tr); pf=wins.손익.sum()/abs(losses.손익.sum()) if abs(losses.손익.sum())>0 else np.inf
    else: wr=pf=0
    return eq,tr,{'return':total,'mdd':mdd,'sharpe':sharpe,'trades':len(tr),'winrate':wr,'pf':pf,'final':eq.Equity.iloc[-1]}

def pct(x): return f'{x*100:,.2f}%'

st.title('📈 APEX AI 주식매매 봇')
st.caption('휴대폰 브라우저용 · AI 확률 + 추세 필터 + ATR 위험관리 백테스트')
st.warning('연구·모의투자용입니다. 수익을 보장하지 않으며 실계좌 주문 기능은 없습니다.')

with st.sidebar:
    st.header('종목 및 데이터')
    ticker=st.text_input('종목코드','005930.KS',help='삼성전자 005930.KS / SK하이닉스 000660.KS / 애플 AAPL').strip().upper()
    interval=st.selectbox('봉 간격',['1d','1h','30m','15m'])
    periods={'1d':['1y','2y','5y','10y','max'],'1h':['1mo','3mo','6mo','1y','2y'],'30m':['1mo','3mo','6mo'],'15m':['1mo','3mo','6mo']}
    period=st.selectbox('데이터 기간',periods[interval],index=min(2,len(periods[interval])-1))
    st.header('AI 설정')
    train_ratio=st.slider('학습 비율',.55,.85,.70,.05); future=st.slider('미래 봉 수',1,10,3); target=st.number_input('상승 판정 기준(%)',0.,10.,.5,.1); threshold=st.slider('매수 확률',.50,.80,.60,.01)
    st.header('위험관리')
    initial=st.number_input('초기자금(원)',100000,1000000000,10000000,100000); risk=st.slider('1회 허용손실(%)',.1,2.,.5,.1); stop=st.slider('손절 ATR',.5,3.,1.5,.1); take=st.slider('익절 ATR',1.,6.,3.,.1); maxbars=st.slider('최대 보유 봉',1,50,10); fee=st.number_input('편도 비용(%)',0.,1.,.10,.01); slip=st.number_input('슬리피지(%)',0.,1.,.05,.01)
    run=st.button('🚀 AI 학습 및 백테스트',type='primary')

if not run:
    st.info('왼쪽 위 메뉴를 열어 종목과 설정을 고른 뒤 실행 버튼을 누르세요.'); st.stop()

try:
    with st.spinner('데이터 수집·AI 학습 중...'):
        raw=load_data(ticker,period,interval); data=make_features(raw,future,target/100); cut=int(len(data)*train_ratio); train=data.iloc[:cut]; test=data.iloc[cut:].copy()
        if len(train)<200 or len(test)<80: raise ValueError(f'학습 {len(train)}개, 검증 {len(test)}개입니다. 더 긴 기간을 선택하세요.')
        model=RandomForestClassifier(n_estimators=350,max_depth=7,min_samples_leaf=8,max_features='sqrt',class_weight='balanced_subsample',n_jobs=-1,random_state=42)
        model.fit(train[FEATURES],train.target); test['probability']=model.predict_proba(test[FEATURES])[:,1]; pred=(test.probability>=threshold).astype(int)
        acc=accuracy_score(test.target,pred)
        try: auc=roc_auc_score(test.target,test.probability)
        except ValueError: auc=np.nan
        eq,tr,m=backtest(test,float(initial),fee/100,slip/100,risk/100,threshold,stop,take,maxbars)
    st.success(f'완료 · 학습 {len(train):,}개 / 검증 {len(test):,}개')
    a,b,c,d=st.columns(4); a.metric('AI 정확도',pct(acc)); b.metric('ROC-AUC',f'{auc:.3f}' if not np.isnan(auc) else 'N/A'); c.metric('전략 수익률',pct(m['return'])); d.metric('최대낙폭',pct(m['mdd']))
    a,b,c,d=st.columns(4); a.metric('최종자산',f"{m['final']:,.0f}원"); b.metric('거래 수',f"{m['trades']}회"); c.metric('승률',pct(m['winrate'])); d.metric('Profit Factor','∞' if np.isinf(m['pf']) else f"{m['pf']:.2f}")
    chart=pd.DataFrame({'전략':eq.Equity/eq.Equity.iloc[0]*100,'매수보유':test.Close/test.Close.iloc[0]*100}); st.line_chart(chart)
    st.subheader('AI가 중요하게 본 지표'); imp=pd.DataFrame({'지표':FEATURES,'중요도':model.feature_importances_}).sort_values('중요도',ascending=False); st.bar_chart(imp.set_index('지표'))
    st.subheader('거래내역')
    if tr.empty: st.warning('조건을 만족한 거래가 없습니다.')
    else:
        show=tr.copy(); show['수익률']=(show['수익률']*100).round(2).astype(str)+'%'; st.dataframe(show,use_container_width=True,hide_index=True)
        st.download_button('거래내역 CSV 다운로드',tr.to_csv(index=False).encode('utf-8-sig'),f'{ticker}_trades.csv','text/csv')
except Exception as e:
    st.error(f'실행 오류: {e}')
