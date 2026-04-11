"""
AMA — Gradient Backprop + Reversal Strength
NIFTY 500 Full Universe Scanner  |  1-Hour Auto-Refresh
Columns: Ticker | Name | HLC3 | AMA | EMA70 | f'(x)% | f''(x)% | f'''(x)% | RSI | Str% | Rating | SIGNAL
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from nifty500 import NIFTY500

st.set_page_config(
    page_title="AMA Gradient — NIFTY 500",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

REFRESH_SECS = 3600  # 1 hour

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #07070e !important;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stSidebar"] { background: #0b0b17 !important; border-right: 1px solid #181828; }
[data-testid="stHeader"] { background: transparent !important; }
.hdr {
    background: #0b0b17; border: 1px solid #181828; border-left: 4px solid #ffd700;
    border-radius: 5px; padding: 12px 20px; margin-bottom: 10px;
    display: flex; justify-content: space-between; align-items: center;
}
.hdr-title { color: #ffd700; font-size: 13px; font-weight: 700; letter-spacing: 3px; }
.hdr-sub   { color: #445; font-size: 9px; letter-spacing: 2px; margin-top: 2px; }
.live-pill {
    display:inline-flex; align-items:center; gap:6px;
    background:#0a1a0a; border:1px solid #1a3a1a; border-radius:3px;
    padding:3px 10px; color:#00ff41; font-size:9px; letter-spacing:2px;
}
.live-dot { width:7px; height:7px; border-radius:50%; background:#00ff41; animation:blink 1.2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.2} }
.stats-bar { display:flex; gap:6px; margin-bottom:10px; }
.stat-box {
    flex:1; background:#0b0b17; border:1px solid #181828;
    border-radius:4px; padding:8px 12px; text-align:center;
}
.stat-lbl { color:#334; font-size:8px; letter-spacing:2px; }
.stat-val { font-size:20px; font-weight:700; margin-top:1px; }
.alert-banner {
    border-radius:4px; padding:7px 14px; margin-bottom:8px;
    display:flex; justify-content:space-between; align-items:center; font-size:10px;
}
.tbl-wrap { background:#0b0b17; border:1px solid #181828; border-radius:5px; overflow:hidden; }
.tbl-scroll { max-height:76vh; overflow-y:auto; }
.tbl-scroll::-webkit-scrollbar { width:4px; }
.tbl-scroll::-webkit-scrollbar-thumb { background:#1a1a2e; border-radius:2px; }
table.ama-tbl { width:100%; border-collapse:collapse; font-size:10px; font-family:'JetBrains Mono',monospace; }
table.ama-tbl thead th {
    background:#0d0d1c; color:#445; font-size:8px; letter-spacing:2px;
    padding:7px 10px; text-align:right; border-bottom:1px solid #181828;
    position:sticky; top:0; z-index:10; white-space:nowrap;
}
table.ama-tbl thead th:nth-child(1),
table.ama-tbl thead th:nth-child(2) { text-align:left; }
table.ama-tbl tbody tr { border-bottom:1px solid #0e0e1c; }
table.ama-tbl tbody tr:hover { background:#0e0e1e; }
table.ama-tbl tbody tr.row-bull { background:rgba(0,255,65,.025); }
table.ama-tbl tbody tr.row-bear { background:rgba(255,46,46,.025); }
table.ama-tbl tbody td {
    padding:5px 10px; text-align:right; color:#9090a0; white-space:nowrap;
}
table.ama-tbl tbody td:nth-child(1),
table.ama-tbl tbody td:nth-child(2) { text-align:left; }
.c-gold  { color:#ffd700 !important; font-weight:700; }
.c-lime  { color:#00ff41 !important; font-weight:700; }
.c-red   { color:#ff2e2e !important; font-weight:700; }
.c-cyan  { color:#00e5ff !important; }
.c-amber { color:#ffc107 !important; }
.c-gray  { color:#667 !important; }
.c-muted { color:#334 !important; }
.badge { display:inline-block; padding:2px 8px; border-radius:2px; font-size:8px; font-weight:700; letter-spacing:1px; }
.b-bull { background:#0a1e0a; color:#00ff41; border:1px solid #1a3a1a; }
.b-bear { background:#1e0a0a; color:#ff2e2e; border:1px solid #3a1a1a; }
.b-none { background:#111; color:#334; border:1px solid #181828; }
.str-wrap { display:flex; align-items:center; gap:5px; justify-content:flex-end; }
.str-bg { background:#111; border-radius:2px; height:4px; width:50px; flex-shrink:0; }
.str-fill { height:4px; border-radius:2px; }
.r-vs { color:#00ff41 !important; }
.r-s  { color:#90ee90 !important; }
.r-m  { color:#ffc107 !important; }
.r-w  { color:#ffa500 !important; }
.r-vw { color:#334 !important; }
div[data-testid="stSidebar"] label { color:#556 !important; font-size:9px !important; letter-spacing:1px !important; }
.stButton > button {
    background:#0b0b17 !important; border:1px solid #181828 !important;
    color:#00e5ff !important; font-family:'JetBrains Mono',monospace !important;
    font-size:10px !important; letter-spacing:2px !important;
    border-radius:3px !important; width:100% !important;
}
.stButton > button:hover { border-color:#00e5ff !important; background:#0a1a2a !important; }
.sidebar-hdr {
    font-size:8px; color:#00e5ff; letter-spacing:3px;
    border-bottom:1px solid #181828; padding-bottom:4px; margin:10px 0 6px;
}
</style>
""", unsafe_allow_html=True)


# ── Math engine ───────────────────────────────────────────────────────────────
def calc_kama(hlc3: np.ndarray, er_len=10, fast=6, slow=7) -> np.ndarray:
    fsc, ssc = 2.0/(fast+1), 2.0/(slow+1)
    n = len(hlc3)
    ama = np.empty(n)
    ama[0] = hlc3[0]
    for i in range(1, n):
        if i < er_len:
            ama[i] = hlc3[i]
            continue
        d = abs(hlc3[i] - hlc3[i-er_len])
        v = np.sum(np.abs(np.diff(hlc3[i-er_len:i+1])))
        er = d/v if v else 0.0
        sc = (er*(fsc-ssc)+ssc)**2
        ama[i] = ama[i-1] + sc*(hlc3[i]-ama[i-1])
    return ama


def calc_rsi(close: np.ndarray, period=14) -> float:
    if len(close) < period+1:
        return 50.0
    deltas = np.diff(close[-(period+2):])
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    ag = np.mean(gains[-period:])
    al = np.mean(losses[-period:])
    if al == 0:
        return 100.0
    return round(100 - 100/(1+ag/al), 1)


def compute_signal(hlc3: np.ndarray, close: np.ndarray, params: dict) -> dict:
    ama   = calc_kama(hlc3, params["er_len"], params["fast"], params["slow"])
    ema70 = float(pd.Series(close).ewm(span=params["ema_len"], adjust=False).mean().iloc[-1])
    rsi   = calc_rsi(close, 14)
    n     = len(ama)

    d1 = np.zeros(n)
    d2 = np.zeros(n)
    d3 = np.zeros(n)
    for i in range(1, n):
        if ama[i] != 0:
            d1[i] = (ama[i]-ama[i-1])/ama[i]*100
    for i in range(2, n):
        if ama[i] != 0:
            d2[i] = (d1[i]-d1[i-1])/ama[i]*1e4
    for i in range(3, n):
        if ama[i] != 0:
            d3[i] = (d2[i]-d2[i-1])/ama[i]*1e6

    er_v = 0.0
    el = params["er_len"]
    if n > el:
        dd = abs(hlc3[-1]-hlc3[-1-el])
        vv = np.sum(np.abs(np.diff(hlc3[-1-el:])))
        er_v = dd/vv if vv else 0.0

    d1v, d2v, d3v = d1[-1], d2[-1], d3[-1]
    gf_bull = (d2v > 0 and d1v < 0) or (d3v > 0 and d2v < 0 and d1v < 0)
    gf_bear = (d2v < 0 and d1v > 0) or (d3v < 0 and d2v > 0 and d1v > 0)

    strength = 0.0
    c1 = c2 = c3 = raw = mx = 0.0
    boost = False

    if gf_bull or gf_bear:
        c1  = abs(d2v)
        c2  = abs(d1v)*abs(d2v)
        c3  = abs(d3v)*0.1
        raw = c1*params["wa"] + c2*params["wb"] + c3*params["wc"]
        lb  = max(0, n-1-params["lookback"])
        mA  = np.max(np.abs(d2[lb:]))
        mD  = np.max(np.abs(d1[lb:])*np.abs(d2[lb:]))
        mJ  = np.max(np.abs(d3[lb:])*0.1)
        mx  = max(1e-9, mA*params["wa"]+mD*params["wb"]+mJ*params["wc"])
        strength = min(100.0, raw/mx*100)
        if abs(d1v) > params["bd1"] and abs(d2v) > params["bd2"]:
            strength = min(100.0, strength*1.25)
            boost = True

    sig = "NONE"
    if params["filt"]:
        if gf_bull and strength >= params["min_str"]:
            sig = "BULL"
        elif gf_bear and strength >= params["min_str"]:
            sig = "BEAR"
    else:
        if gf_bull:
            sig = "BULL"
        elif gf_bear:
            sig = "BEAR"

    return {
        "hlc3":     round(float(hlc3[-1]), 2),
        "ama":      round(float(ama[-1]), 2),
        "ema70":    round(ema70, 2),
        "d1":       round(d1v, 4),
        "d2":       round(d2v, 6),
        "d3":       round(d3v, 4),
        "rsi":      rsi,
        "strength": round(strength, 1),
        "signal":   sig,
        "gf_bull":  gf_bull,
        "gf_bear":  gf_bear,
        "boost":    boost,
        "er":       round(er_v, 4),
    }


def rating(s: float) -> tuple:
    if s >= 80: return "VERY STRONG", "r-vs"
    if s >= 60: return "STRONG",      "r-s"
    if s >= 40: return "MODERATE",    "r-m"
    if s >= 20: return "WEAK",        "r-w"
    return "VERY WEAK", "r-vw"


def str_color(s: float, bull: bool) -> str:
    if s >= 80: return "#00ff41" if bull else "#ff2e2e"
    if s >= 60: return "#90ee90" if bull else "#ff7070"
    if s >= 40: return "#ffc107"
    return "#ffa500"


@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch(ticker: str, period: str, interval: str):
    try:
        df = yf.download(f"{ticker}.NS", period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"])
        return df if len(df) > 20 else None
    except Exception:
        return None


def process(ticker: str, params: dict):
    df = fetch(ticker, params["period"], params["interval"])
    if df is None:
        return None
    hlc3  = ((df["High"]+df["Low"]+df["Close"])/3).values.astype(float)
    close = df["Close"].values.astype(float)
    if len(hlc3) < params["er_len"]+5:
        return None
    try:
        sig = compute_signal(hlc3, close, params)
    except Exception:
        return None
    price = float(close[-1])
    prev  = float(close[-2]) if len(close) > 1 else price
    return {
        "ticker": ticker,
        "name":   NIFTY500.get(ticker, ticker),
        "price":  price,
        "chg":    (price-prev)/prev*100 if prev else 0.0,
        **sig,
    }


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("results",[]),("alerts",[]),("last_scan",None),("scan_done",False)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-hdr">UNIVERSE</div>', unsafe_allow_html=True)
    mode = st.radio("", ["NIFTY 500 (All)","NIFTY 50","NIFTY Next 50","Custom"],
                    label_visibility="collapsed")
    tickers_all = list(NIFTY500.keys())
    if mode == "NIFTY 50":
        scan_list = tickers_all[:50]
    elif mode == "NIFTY Next 50":
        scan_list = tickers_all[50:100]
    elif mode == "Custom":
        scan_list = st.multiselect("Tickers", tickers_all,
                                   default=["RELIANCE","TCS","INFY","HDFCBANK","SBIN"])
        if not scan_list:
            scan_list = tickers_all[:50]
    else:
        scan_list = tickers_all

    st.markdown('<div class="sidebar-hdr">AMA CORE</div>', unsafe_allow_html=True)
    er_len  = st.slider("ER Window",       3, 30, 10)
    fast_p  = st.slider("Fast SC Period",  2, 10,  6)
    slow_p  = st.slider("Slow SC Period",  5, 15,  7)
    ema_len = st.slider("EMA Length",     20,200, 70)

    st.markdown('<div class="sidebar-hdr">REVERSAL STRENGTH</div>', unsafe_allow_html=True)
    lookback = st.slider("Lookback",       5, 50, 20)
    min_str  = st.slider("Min Strength %", 0,100, 50, step=5)
    filt_on  = st.toggle("Strength Filter", True)
    wa       = st.slider("Wt Accel (C1)",  0.10, 1.00, 0.35, step=0.05)
    wb       = st.slider("Wt Diverge (C2)",0.001,0.05, 0.012, step=0.001, format="%.3f")
    wc       = st.slider("Wt Jerk (C3)",   0.10, 1.00, 0.50, step=0.05)
    bd1      = st.slider("Boost |f'| thr", 0.5,  3.0,  1.0,  step=0.1)
    bd2      = st.slider("Boost |f''| thr",0.1,  2.0,  0.5,  step=0.1)

    st.markdown('<div class="sidebar-hdr">DATA</div>', unsafe_allow_html=True)
    period   = st.selectbox("History",  ["3mo","6mo","1y","2y"], index=0)
    interval = st.selectbox("Interval", ["1d","1wk"], index=0)

    st.markdown('<div class="sidebar-hdr">ALERTS</div>', unsafe_allow_html=True)
    alert_thr = st.slider("Alert Threshold %", 50, 100, 80, step=5)
    auto_ref  = st.toggle("Auto Refresh (1hr)", False)

    st.markdown("<br>", unsafe_allow_html=True)
    run_btn = st.button("⚡  SCAN NIFTY 500")

params = dict(
    er_len=er_len, fast=fast_p, slow=slow_p, ema_len=ema_len,
    lookback=lookback, min_str=min_str, filt=filt_on,
    wa=wa, wb=wb, wc=wc, bd1=bd1, bd2=bd2,
    period=period, interval=interval,
)

# ── Header ────────────────────────────────────────────────────────────────────
now_s = datetime.now().strftime("%H:%M:%S  %d %b %Y")
mo = datetime.now()
mkt_open = (mo.weekday() < 5 and
            timedelta(hours=9, minutes=15)
            <= timedelta(hours=mo.hour, minutes=mo.minute)
            <= timedelta(hours=15, minutes=30))
mkt_col = "#00ff41" if mkt_open else "#ff4444"
mkt_lbl = "NSE OPEN" if mkt_open else "NSE CLOSED"

ls = st.session_state.last_scan
nr_txt = ""
if ls and auto_ref:
    rem = max(0, REFRESH_SECS-(datetime.now()-ls).seconds)
    nr_txt = f"  ◈  NEXT REFRESH {rem//60:02d}:{rem%60:02d}"

st.markdown(f"""
<div class="hdr">
  <div>
    <div class="hdr-title">⚡ AMA v3.0 — GRADIENT BACKPROP + REVERSAL STRENGTH</div>
    <div class="hdr-sub">NIFTY 500 UNIVERSE  ◈  KAMA + f\'(x) f\'\'(x) f\'\'\'(x)  ◈  1-HOUR REFRESH{nr_txt}</div>
  </div>
  <div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;">
    <div class="live-pill"><span class="live-dot"></span>LIVE</div>
    <div style="font-size:9px;color:#445;">{now_s}</div>
    <div style="font-size:8px;color:{mkt_col};letter-spacing:2px;">{mkt_lbl}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_ref and ls and (datetime.now()-ls).seconds >= REFRESH_SECS:
    run_btn = True
if not st.session_state.scan_done:
    run_btn = True

# ── Scan ──────────────────────────────────────────────────────────────────────
if run_btn:
    results = []
    total   = len(scan_list)
    prog    = st.progress(0, text="Initializing scan…")
    for idx, tk in enumerate(scan_list):
        prog.progress((idx+1)/total, text=f"⚡ {tk}  {idx+1}/{total}")
        r = process(tk, params)
        if r:
            results.append(r)
    prog.empty()

    new_alerts = []
    for r in results:
        if r["signal"] != "NONE" and r["strength"] >= alert_thr:
            new_alerts.append({
                "ts":     datetime.now().strftime("%H:%M:%S"),
                "ticker": r["ticker"],
                "name":   r["name"],
                "signal": r["signal"],
                "str":    r["strength"],
                "price":  r["price"],
            })
    st.session_state.alerts    = (new_alerts + st.session_state.alerts)[:100]
    st.session_state.results   = results
    st.session_state.last_scan = datetime.now()
    st.session_state.scan_done = True

results = st.session_state.results

# ── Stats bar ─────────────────────────────────────────────────────────────────
if results:
    n_bull = sum(1 for r in results if r["signal"]=="BULL")
    n_bear = sum(1 for r in results if r["signal"]=="BEAR")
    n_vs   = sum(1 for r in results if r["strength"]>=80)
    avg_s  = np.mean([r["strength"] for r in results if r["signal"]!="NONE"] or [0])
    ls_str = st.session_state.last_scan.strftime("%H:%M:%S") if st.session_state.last_scan else "--"

    st.markdown(f"""
    <div class="stats-bar">
      <div class="stat-box"><div class="stat-lbl">SCANNED</div>
        <div class="stat-val" style="color:#00e5ff;">{len(results)}</div></div>
      <div class="stat-box"><div class="stat-lbl">↑ BULL</div>
        <div class="stat-val" style="color:#00ff41;">{n_bull}</div></div>
      <div class="stat-box"><div class="stat-lbl">↓ BEAR</div>
        <div class="stat-val" style="color:#ff2e2e;">{n_bear}</div></div>
      <div class="stat-box"><div class="stat-lbl">STRONG ≥80%</div>
        <div class="stat-val" style="color:#ffd700;">{n_vs}</div></div>
      <div class="stat-box"><div class="stat-lbl">AVG STR</div>
        <div class="stat-val" style="color:#ffc107;">{avg_s:.1f}%</div></div>
      <div class="stat-box"><div class="stat-lbl">LAST SCAN</div>
        <div class="stat-val" style="color:#556;font-size:13px;">{ls_str}</div></div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.alerts:
        a   = st.session_state.alerts[0]
        ba  = a["signal"]=="BULL"
        ca  = "#00ff41" if ba else "#ff2e2e"
        bda = "#1a3a1a" if ba else "#3a1a1a"
        bga = "#0a1a0a" if ba else "#1a0a0a"
        rt, _ = rating(a["str"])
        st.markdown(f"""
        <div class="alert-banner"
             style="background:{bga};border:1px solid {bda};border-left:4px solid {ca};">
          <div>
            <span style="color:{ca};font-weight:700;font-size:11px;">
              {'↑' if ba else '↓'} ALERT — {a['ticker']}
            </span>
            <span style="color:#667;font-size:9px;margin-left:10px;">
              {a['name']}  ◈  {rt}  ◈  ₹{a['price']:,.0f}  ◈  {a['ts']}
            </span>
          </div>
          <span style="color:{ca};font-size:15px;font-weight:700;">{a['str']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

# ── Filter / sort ─────────────────────────────────────────────────────────────
if results:
    fc1, fc2, fc3, fc4 = st.columns([3,2,2,2])
    with fc1:
        search = st.text_input("", placeholder="Search ticker or company…",
                               label_visibility="collapsed")
    with fc2:
        sig_f = st.selectbox("", ["All","↑ Bull","↓ Bear","Strong ≥80%","Signals Only"],
                             label_visibility="collapsed")
    with fc3:
        sort_f = st.selectbox("", ["Strength ↓","RSI ↓","Change % ↓","Price ↓","Ticker A→Z"],
                              label_visibility="collapsed")
    with fc4:
        rsi_f = st.select_slider("RSI", ["All","OB >70","OS <30","Neutral 30-70"],
                                 value="All", label_visibility="collapsed")

    rows = list(results)
    if search:
        s = search.upper()
        rows = [r for r in rows if s in r["ticker"] or s in r["name"].upper()]
    if sig_f == "↑ Bull":          rows = [r for r in rows if r["signal"]=="BULL"]
    elif sig_f == "↓ Bear":        rows = [r for r in rows if r["signal"]=="BEAR"]
    elif sig_f == "Strong ≥80%":   rows = [r for r in rows if r["strength"]>=80]
    elif sig_f == "Signals Only":  rows = [r for r in rows if r["signal"]!="NONE"]
    if rsi_f == "OB >70":          rows = [r for r in rows if r["rsi"]>=70]
    elif rsi_f == "OS <30":        rows = [r for r in rows if r["rsi"]<=30]
    elif rsi_f == "Neutral 30-70": rows = [r for r in rows if 30<r["rsi"]<70]

    if sort_f == "Strength ↓":
        rows.sort(key=lambda x:(x["signal"]!="NONE", x["strength"]), reverse=True)
    elif sort_f == "RSI ↓":
        rows.sort(key=lambda x: x["rsi"], reverse=True)
    elif sort_f == "Change % ↓":
        rows.sort(key=lambda x: abs(x["chg"]), reverse=True)
    elif sort_f == "Price ↓":
        rows.sort(key=lambda x: x["price"], reverse=True)
    elif sort_f == "Ticker A→Z":
        rows.sort(key=lambda x: x["ticker"])

    # ── Table HTML ────────────────────────────────────────────────────────────
    def _dc(v):
        c = "c-lime" if v > 0 else ("c-red" if v < 0 else "c-muted")
        s = ("+" if v > 0 else "") + f"{v:.4f}"
        return f'<span class="{c}">{s}</span>'

    def _rsi(v):
        c = "c-red" if v>=70 else ("c-lime" if v<=30 else "c-gray")
        return f'<span class="{c}">{v:.1f}</span>'

    def _str(v, bull):
        if v == 0:
            return '<span class="c-muted">—</span>'
        col = str_color(v, bull)
        return (f'<div class="str-wrap">'
                f'<span style="color:{col};font-weight:700;min-width:34px;">{v:.1f}%</span>'
                f'<div class="str-bg"><div class="str-fill" style="width:{v}%;background:{col}"></div></div>'
                f'</div>')

    def _rt(v):
        if v == 0:
            return '<span class="c-muted">—</span>'
        rt, cls = rating(v)
        return f'<span class="{cls}" style="font-size:9px;">{rt}</span>'

    tbody = ""
    for r in rows:
        bull = r["signal"] == "BULL"
        bear = r["signal"] == "BEAR"
        rc   = "row-bull" if bull else ("row-bear" if bear else "")
        bc   = "b-bull" if bull else ("b-bear" if bear else "b-none")
        bt   = "↑ BULL" if bull else ("↓ BEAR" if bear else "—")
        cc   = "c-lime" if r["chg"]>=0 else "c-red"
        cs   = ("+" if r["chg"]>=0 else "")+f"{r['chg']:.2f}%"
        p_s  = f"₹{r['price']:,.0f}" if r["price"]>=100 else f"₹{r['price']:,.2f}"

        tbody += (
            f'<tr class="{rc}">'
            f'<td class="c-gold">{r["ticker"]}</td>'
            f'<td style="color:#778;font-size:9px;max-width:140px;overflow:hidden;text-overflow:ellipsis;">{r["name"]}</td>'
            f'<td>₹{r["hlc3"]:,.2f}</td>'
            f'<td class="c-cyan">₹{r["ama"]:,.2f}</td>'
            f'<td class="c-gray">₹{r["ema70"]:,.2f}</td>'
            f'<td>{_dc(r["d1"])}</td>'
            f'<td>{_dc(r["d2"])}</td>'
            f'<td>{_dc(r["d3"])}</td>'
            f'<td>{_rsi(r["rsi"])}</td>'
            f'<td>{_str(r["strength"], bull)}</td>'
            f'<td>{_rt(r["strength"])}</td>'
            f'<td style="text-align:center;"><span class="badge {bc}">{bt}</span></td>'
            f'</tr>'
        )

    st.markdown(f"""
    <div class="tbl-wrap">
      <div class="tbl-scroll">
        <table class="ama-tbl">
          <thead><tr>
            <th>TICKER</th><th>NAME</th><th>HLC3</th>
            <th>AMA</th><th>EMA{ema_len}</th>
            <th>f'(x)%</th><th>f''(x)%</th><th>f'''(x)%</th>
            <th>RSI</th><th>STR%</th><th>RATING</th><th>SIGNAL</th>
          </tr></thead>
          <tbody>{tbody}</tbody>
        </table>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer row ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    bt1, bt2 = st.columns([4,1])
    with bt1:
        ls_s = st.session_state.last_scan.strftime("%d %b %Y %H:%M:%S") \
               if st.session_state.last_scan else "—"
        st.markdown(
            f'<div style="font-size:9px;color:#334;padding-top:8px;">'
            f'{len(rows)} rows  ◈  {len(results)} scanned  ◈  Last: {ls_s}'
            f'  ◈  Refresh: 1 hour</div>',
            unsafe_allow_html=True)
    with bt2:
        df_out = pd.DataFrame([{
            "Ticker":       r["ticker"],
            "Name":         r["name"],
            "Price":        round(r["price"],2),
            "Chg%":         round(r["chg"],2),
            "HLC3":         r["hlc3"],
            "AMA":          r["ama"],
            f"EMA{ema_len}":r["ema70"],
            "f'(x)%":       r["d1"],
            "f''(x)%":      r["d2"],
            "f'''(x)%":     r["d3"],
            "RSI":          r["rsi"],
            "Str%":         r["strength"],
            "Rating":       rating(r["strength"])[0] if r["signal"]!="NONE" else "—",
            "Signal":       r["signal"],
            "ER":           r["er"],
        } for r in rows])
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button("⬇ CSV", df_out.to_csv(index=False),
                           file_name=f"AMA_N500_{ts}.csv",
                           mime="text/csv", use_container_width=True)

    # ── Alert history ─────────────────────────────────────────────────────────
    if st.session_state.alerts:
        with st.expander(f"🔔  ALERT HISTORY  ({len(st.session_state.alerts)} fired)"):
            ah = ""
            for a in st.session_state.alerts[:50]:
                ba = a["signal"]=="BULL"
                ca = "#00ff41" if ba else "#ff2e2e"
                rt, _ = rating(a["str"])
                ah += (
                    f'<tr>'
                    f'<td style="color:#445;">{a["ts"]}</td>'
                    f'<td class="c-gold">{a["ticker"]}</td>'
                    f'<td style="color:#778;font-size:9px;">{a["name"]}</td>'
                    f'<td><span class="badge {"b-bull" if ba else "b-bear"}">{"↑ BULL" if ba else "↓ BEAR"}</span></td>'
                    f'<td style="color:{ca};font-weight:700;">{a["str"]:.1f}%</td>'
                    f'<td style="color:{ca};font-size:9px;">{rt}</td>'
                    f'<td style="color:#667;">₹{a["price"]:,.0f}</td>'
                    f'</tr>'
                )
            st.markdown(
                f'<div class="tbl-wrap"><table class="ama-tbl">'
                f'<thead><tr><th>TIME</th><th>TICKER</th><th>NAME</th>'
                f'<th>SIGNAL</th><th>STR%</th><th>RATING</th><th>PRICE</th></tr></thead>'
                f'<tbody>{ah}</tbody></table></div>',
                unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:60px;color:#334;font-size:11px;
         border:1px solid #181828;border-radius:5px;background:#0b0b17;margin-top:10px;">
      <div style="font-size:28px;margin-bottom:12px;">⚡</div>
      Click <b style="color:#00e5ff;">SCAN NIFTY 500</b> in the sidebar to begin.<br>
      <span style="font-size:9px;color:#223;">~500 equities  ◈  yfinance  ◈  1-hr cache  ◈  KAMA gradient engine</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;color:#223;font-size:8px;letter-spacing:2px;
     border-top:1px solid #181828;padding:8px 0;margin-top:8px;">
  AMA v3.0  ◈  GRADIENT BACKPROP  ◈  NIFTY 500  ◈  yfinance  ◈  1-HR REFRESH  ◈  NOT INVESTMENT ADVICE
</div>
""", unsafe_allow_html=True)

if auto_ref and st.session_state.last_scan:
    if (datetime.now()-st.session_state.last_scan).seconds >= REFRESH_SECS:
        time.sleep(1)
        st.rerun()
