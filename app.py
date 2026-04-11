"""
AMA  — Gradient Backprop + Reversal Strength
NIFTY 500 Full Universe Scanner | 1-Hour Auto-Refresh | White Theme
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
    initial_sidebar_state="collapsed",
)

REFRESH_SECS = 3600

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #f8f9fc !important;
    font-family: 'Inter', sans-serif !important;
    color: #1a1d2e !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }
div[data-testid="stHorizontalBlock"] { gap: 10px !important; }

/* ── Top Nav Bar ── */
.nav-bar {
    background: #ffffff;
    border: 1px solid #e8eaf0;
    border-radius: 10px;
    padding: 10px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.nav-brand { display: flex; align-items: center; gap: 12px; }
.nav-logo {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, #1a1d2e 0%, #2d3561 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; color: #f59e0b; font-weight: 700;
}
.nav-title { font-size: 14px; font-weight: 700; color: #1a1d2e; letter-spacing: -0.3px; }
.nav-sub { font-size: 10px; color: #94a3b8; margin-top: 1px; letter-spacing: 0.5px; }
.nav-right { display: flex; align-items: center; gap: 14px; }
.nav-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: 20px; padding: 3px 10px;
    font-size: 10px; font-weight: 600; color: #16a34a; letter-spacing: 0.5px;
}
.live-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #16a34a;
    animation: pulse 1.4s infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }
.nav-time { font-size: 11px; color: #64748b; font-family: 'JetBrains Mono', monospace; }
.mkt-open  { background:#f0fdf4; border:1px solid #bbf7d0; color:#16a34a; border-radius:20px; padding:3px 10px; font-size:10px; font-weight:600; }
.mkt-close { background:#fef2f2; border:1px solid #fecaca; color:#dc2626; border-radius:20px; padding:3px 10px; font-size:10px; font-weight:600; }

/* ── Toolbar (filter row) ── */
.toolbar {
    background: #ffffff; border: 1px solid #e8eaf0; border-radius: 10px;
    padding: 10px 16px; margin-bottom: 10px; display: flex;
    align-items: center; gap: 10px; flex-wrap: wrap;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* ── Stat cards ── */
.stats-row { display: flex; gap: 10px; margin-bottom: 10px; }
.stat-card {
    flex: 1; background: #ffffff; border: 1px solid #e8eaf0;
    border-radius: 10px; padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.stat-card-accent { border-top: 3px solid var(--accent); }
.sc-label { font-size: 10px; font-weight: 500; color: #94a3b8; letter-spacing: 0.8px; text-transform: uppercase; }
.sc-val { font-size: 22px; font-weight: 700; margin-top: 2px; color: var(--accent); }
.sc-sub { font-size: 10px; color: #cbd5e1; margin-top: 1px; }

/* ── Alert banner ── */
.alert-box {
    border-radius: 10px; padding: 10px 16px; margin-bottom: 10px;
    display: flex; justify-content: space-between; align-items: center;
    border-left: 4px solid var(--alert-col);
    background: var(--alert-bg);
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

/* ── Main table ── */
.tbl-card {
    background: #ffffff; border: 1px solid #e8eaf0; border-radius: 10px;
    overflow: hidden; box-shadow: 0 1px 6px rgba(0,0,0,0.05);
}
.tbl-header {
    background: #f8f9fc; border-bottom: 1px solid #e8eaf0;
    padding: 8px 14px; display: flex; justify-content: space-between; align-items: center;
}
.tbl-title { font-size: 11px; font-weight: 600; color: #475569; letter-spacing: 0.5px; }
.tbl-count { font-size: 10px; color: #94a3b8; }
.tbl-scroll { max-height: 74vh; overflow-y: auto; }
.tbl-scroll::-webkit-scrollbar { width: 4px; }
.tbl-scroll::-webkit-scrollbar-track { background: #f8f9fc; }
.tbl-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

table.ama { width: 100%; border-collapse: collapse; font-size: 11px; }
table.ama thead th {
    background: #f8f9fc; color: #64748b; font-size: 9px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
    padding: 8px 12px; text-align: right; border-bottom: 1px solid #e8eaf0;
    position: sticky; top: 0; z-index: 5; white-space: nowrap;
}
table.ama thead th:nth-child(1){ text-align:left; min-width:90px; }
table.ama thead th.th-sig { text-align:center; }

table.ama tbody tr {
    border-bottom: 1px solid #f1f5f9;
    transition: background 0.1s;
}
table.ama tbody tr:hover { background: #f8faff; }
table.ama tbody tr.bull-row { background: #fafffe; }
table.ama tbody tr.bear-row { background: #fffafa; }
table.ama tbody tr.bull-row:hover { background: #f0fdf8; }
table.ama tbody tr.bear-row:hover { background: #fff5f5; }

table.ama tbody td {
    padding: 7px 12px; text-align: right; color: #334155;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; white-space: nowrap;
}
table.ama tbody td:nth-child(1) { text-align:left; font-family:'Inter',sans-serif; }
table.ama tbody td.td-sig { text-align:center; }

/* cell colours */
.tk   { font-weight: 700; color: #1a1d2e; font-size: 11px; letter-spacing: -0.2px; }
.tk a { text-decoration: none; color: inherit; }
.pos  { color: #16a34a; font-weight: 600; }
.neg  { color: #dc2626; font-weight: 600; }
.neu  { color: #64748b; }
.hl-cyan  { color: #0891b2; font-weight: 600; }
.hl-slate { color: #475569; }

/* badges */
.badge {
    display: inline-flex; align-items: center; gap: 3px;
    padding: 2px 8px; border-radius: 20px; font-size: 9px;
    font-weight: 700; letter-spacing: 0.5px; font-family: 'Inter', sans-serif;
}
.b-bull { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.b-bear { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
.b-none { background: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0; }

/* strength bar */
.str-cell { display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
.str-num  { font-weight: 600; font-size: 11px; min-width: 36px; text-align: right; }
.str-track{ height: 4px; width: 44px; background: #e2e8f0; border-radius: 3px; flex-shrink: 0; }
.str-fill { height: 4px; border-radius: 3px; }

/* rating text */
.rt-vs { color: #15803d; font-weight: 600; font-size: 10px; }
.rt-s  { color: #16a34a; font-weight: 500; font-size: 10px; }
.rt-m  { color: #d97706; font-weight: 500; font-size: 10px; }
.rt-w  { color: #ea580c; font-weight: 500; font-size: 10px; }
.rt-vw { color: #94a3b8; font-weight: 400; font-size: 10px; }

/* RSI colouring */
.rsi-ob { color: #dc2626; font-weight: 600; }
.rsi-os { color: #16a34a; font-weight: 600; }
.rsi-n  { color: #475569; }

/* ── Streamlit widget overrides ── */
.stButton > button {
    background: #1a1d2e !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 12px !important;
    font-weight: 600 !important; padding: 8px 20px !important;
    letter-spacing: 0.3px !important; transition: opacity .2s !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stDownloadButton > button {
    background: #f1f5f9 !important; color: #334155 !important;
    border: 1px solid #e2e8f0 !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 11px !important;
    font-weight: 500 !important;
}
div[data-testid="stSelectbox"] > div,
div[data-testid="stTextInput"] > div > div {
    border-radius: 8px !important; border-color: #e2e8f0 !important;
    background: #ffffff !important; font-size: 12px !important;
}
.stTextInput input { font-size: 12px !important; }
.stProgress > div > div > div > div { background: #2d3561 !important; border-radius: 4px !important; }
label[data-testid="stWidgetLabel"] { font-size: 11px !important; color: #64748b !important; }
div[data-testid="stToggle"] { margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


# ── Math engine ────────────────────────────────────────────────────────────────
def calc_kama(hlc3: np.ndarray, er_len=10, fast=6, slow=7) -> np.ndarray:
    fsc, ssc = 2.0 / (fast + 1), 2.0 / (slow + 1)
    n = len(hlc3)
    ama = np.empty(n)
    ama[0] = hlc3[0]
    for i in range(1, n):
        if i < er_len:
            ama[i] = hlc3[i]; continue
        d = abs(hlc3[i] - hlc3[i - er_len])
        v = np.sum(np.abs(np.diff(hlc3[i - er_len:i + 1])))
        er = d / v if v else 0.0
        sc = (er * (fsc - ssc) + ssc) ** 2
        ama[i] = ama[i - 1] + sc * (hlc3[i] - ama[i - 1])
    return ama


def calc_rsi(close: np.ndarray, period=14) -> float:
    if len(close) < period + 1:
        return 50.0
    deltas = np.diff(close[-(period + 2):])
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    ag, al = np.mean(gains[-period:]), np.mean(losses[-period:])
    return round(100.0 if al == 0 else 100 - 100 / (1 + ag / al), 1)


def compute_signal(hlc3: np.ndarray, close: np.ndarray, p: dict) -> dict:
    ama  = calc_kama(hlc3, p["er_len"], p["fast"], p["slow"])
    ema  = float(pd.Series(close).ewm(span=p["ema_len"], adjust=False).mean().iloc[-1])
    rsi  = calc_rsi(close, 14)
    n    = len(ama)

    d1 = np.zeros(n); d2 = np.zeros(n); d3 = np.zeros(n)
    for i in range(1, n):
        if ama[i]: d1[i] = (ama[i] - ama[i-1]) / ama[i] * 100
    for i in range(2, n):
        if ama[i]: d2[i] = (d1[i] - d1[i-1]) / ama[i] * 1e4
    for i in range(3, n):
        if ama[i]: d3[i] = (d2[i] - d2[i-1]) / ama[i] * 1e6

    el = p["er_len"]
    er_v = 0.0
    if n > el:
        dd = abs(hlc3[-1] - hlc3[-1 - el])
        vv = np.sum(np.abs(np.diff(hlc3[-1 - el:])))
        er_v = dd / vv if vv else 0.0

    d1v, d2v, d3v = d1[-1], d2[-1], d3[-1]
    gfb = (d2v > 0 and d1v < 0) or (d3v > 0 and d2v < 0 and d1v < 0)
    gfr = (d2v < 0 and d1v > 0) or (d3v < 0 and d2v > 0 and d1v > 0)

    strength = 0.0; boost = False
    c1 = c2 = c3 = raw = mx = 0.0
    if gfb or gfr:
        c1  = abs(d2v); c2 = abs(d1v) * abs(d2v); c3 = abs(d3v) * 0.1
        raw = c1 * p["wa"] + c2 * p["wb"] + c3 * p["wc"]
        lb  = max(0, n - 1 - p["lookback"])
        mA  = np.max(np.abs(d2[lb:]))
        mD  = np.max(np.abs(d1[lb:]) * np.abs(d2[lb:]))
        mJ  = np.max(np.abs(d3[lb:]) * 0.1)
        mx  = max(1e-9, mA * p["wa"] + mD * p["wb"] + mJ * p["wc"])
        strength = min(100.0, raw / mx * 100)
        if abs(d1v) > p["bd1"] and abs(d2v) > p["bd2"]:
            strength = min(100.0, strength * 1.25); boost = True

    sig = "NONE"
    if p["filt"]:
        if gfb and strength >= p["min_str"]:  sig = "BULL"
        elif gfr and strength >= p["min_str"]: sig = "BEAR"
    else:
        if gfb:  sig = "BULL"
        elif gfr: sig = "BEAR"

    return {
        "hlc3": round(float(hlc3[-1]), 2), "ama": round(float(ama[-1]), 2),
        "ema70": round(ema, 2), "d1": round(d1v, 4),
        "d2": round(d2v, 6),   "d3": round(d3v, 4),
        "rsi": rsi, "strength": round(strength, 1),
        "signal": sig, "gf_bull": gfb, "gf_bear": gfr,
        "boost": boost, "er": round(er_v, 4),
    }


def get_rating(s: float):
    if s >= 80: return "VERY STRONG", "rt-vs", "#15803d"
    if s >= 60: return "STRONG",      "rt-s",  "#16a34a"
    if s >= 40: return "MODERATE",    "rt-m",  "#d97706"
    if s >= 20: return "WEAK",        "rt-w",  "#ea580c"
    return "VERY WEAK", "rt-vw", "#94a3b8"


def str_col(s: float, bull: bool) -> str:
    if s >= 80: return "#15803d" if bull else "#b91c1c"
    if s >= 60: return "#16a34a" if bull else "#dc2626"
    if s >= 40: return "#d97706"
    return "#ea580c"


# ── Data fetch (1-hr TTL) ──────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_ticker(ticker: str, period: str, interval: str) -> pd.DataFrame | None:
    for attempt in range(3):
        try:
            df = yf.download(
                f"{ticker}.NS", period=period, interval=interval,
                progress=False, auto_adjust=True,
            )
            if df is None or df.empty:
                return None
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=["Close"])
            return df if len(df) > 20 else None
        except Exception:
            if attempt < 2: time.sleep(1)
    return None


def process(ticker: str, p: dict) -> dict | None:
    df = fetch_ticker(ticker, p["period"], p["interval"])
    if df is None: return None
    try:
        h = df["High"].values.astype(float)
        l = df["Low"].values.astype(float)
        c = df["Close"].values.astype(float)
        hlc3  = (h + l + c) / 3
        if len(hlc3) < p["er_len"] + 5: return None
        sig   = compute_signal(hlc3, c, p)
        price = float(c[-1])
        prev  = float(c[-2]) if len(c) > 1 else price
        return {
            "ticker": ticker,
            "name":   NIFTY500.get(ticker, ticker),
            "price":  price, "prev": prev,
            "chg":    (price - prev) / prev * 100 if prev else 0.0,
            **sig,
        }
    except Exception:
        return None


# ── Session state ──────────────────────────────────────────────────────────────
for k, v in [("results",[]),("alerts",[]),("last_scan",None),("scanned",False)]:
    if k not in st.session_state: st.session_state[k] = v

# ── Default params ─────────────────────────────────────────────────────────────
params = dict(
    er_len=10, fast=6, slow=7, ema_len=70,
    lookback=20, min_str=50, filt=True,
    wa=0.35, wb=0.012, wc=0.50, bd1=1.0, bd2=0.5,
    period="3mo", interval="1d",
)

# ── NAV BAR ───────────────────────────────────────────────────────────────────
now  = datetime.now()
mkt  = (now.weekday() < 5 and
        timedelta(hours=9, minutes=15)
        <= timedelta(hours=now.hour, minutes=now.minute)
        <= timedelta(hours=15, minutes=30))
mkt_html = (f'<span class="mkt-open">● NSE OPEN</span>' if mkt
            else f'<span class="mkt-close">● NSE CLOSED</span>')

ls   = st.session_state.last_scan
nxt  = ""
if ls:
    rem = max(0, REFRESH_SECS - int((now - ls).total_seconds()))
    nxt = f"Next refresh {rem//60:02d}:{rem%60:02d}"

st.markdown(f"""
<div class="nav-bar">
  <div class="nav-brand">
    <div class="nav-logo">⚡</div>
    <div>
      <div class="nav-title">AMA v3.0 — Gradient Backprop + Reversal Strength</div>
      <div class="nav-sub">NIFTY 500 UNIVERSE  ·  KAMA  ·  f'(x) f''(x) f'''(x)  ·  1-HR REFRESH  ·  {nxt}</div>
    </div>
  </div>
  <div class="nav-right">
    <div class="nav-badge"><span class="live-dot"></span>LIVE</div>
    <span class="nav-time">{now.strftime('%H:%M:%S  %d %b %Y')}</span>
    {mkt_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ── CONTROLS ROW ──────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2.5, 1.5, 1.5, 1.5, 1.2, 1.2, 1, 1])
with c1:
    search = st.text_input("", placeholder="🔍  Search ticker or company…", label_visibility="collapsed")
with c2:
    universe = st.selectbox("", ["NIFTY 500 (All)", "NIFTY 50", "NIFTY Next 50", "Custom"],
                            label_visibility="collapsed")
with c3:
    sig_f = st.selectbox("", ["All Signals", "↑ Bull Only", "↓ Bear Only",
                               "Strong ≥80%", "Has Signal"],
                          label_visibility="collapsed")
with c4:
    sort_f = st.selectbox("", ["Strength ↓", "Change % ↓", "RSI ↓", "Price ↓", "A → Z"],
                           label_visibility="collapsed")
with c5:
    rsi_f = st.selectbox("", ["RSI: All", "OB >70", "OS <30", "Neutral"],
                          label_visibility="collapsed")
with c6:
    period = st.selectbox("", ["3mo", "6mo", "1y", "2y"], label_visibility="collapsed")
with c7:
    min_str_ui = st.selectbox("", ["Min 50%", "Min 60%", "Min 70%", "Min 80%", "No Filter"],
                               label_visibility="collapsed")
with c8:
    run_btn = st.button("⚡  Scan", use_container_width=True)

# custom universe picker
if universe == "Custom":
    tickers_all = list(NIFTY500.keys())
    scan_list = st.multiselect("Select tickers:", tickers_all,
                                default=["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"])
    if not scan_list: scan_list = tickers_all[:50]
elif universe == "NIFTY 50":
    scan_list = list(NIFTY500.keys())[:50]
elif universe == "NIFTY Next 50":
    scan_list = list(NIFTY500.keys())[50:100]
else:
    scan_list = list(NIFTY500.keys())

min_str_map = {"Min 50%": 50, "Min 60%": 60, "Min 70%": 70, "Min 80%": 80, "No Filter": 0}
params["min_str"] = min_str_map[min_str_ui]
params["filt"]    = params["min_str"] > 0
params["period"]  = period

# ── AUTO-REFRESH CHECK ─────────────────────────────────────────────────────────
if ls and int((now - ls).total_seconds()) >= REFRESH_SECS:
    run_btn = True
if not st.session_state.scanned:
    run_btn = True

# ── SCAN ──────────────────────────────────────────────────────────────────────
if run_btn:
    prog = st.progress(0, text="Starting NIFTY 500 scan…")
    results, failed = [], []
    for idx, tk in enumerate(scan_list):
        prog.progress((idx + 1) / len(scan_list),
                      text=f"Fetching  {tk}  ({idx+1}/{len(scan_list)})")
        r = process(tk, params)
        if r: results.append(r)
        else: failed.append(tk)
    prog.empty()

    alerts = []
    for r in results:
        if r["signal"] != "NONE" and r["strength"] >= 80:
            alerts.append({
                "ts": now.strftime("%H:%M:%S"), "ticker": r["ticker"],
                "name": r["name"], "signal": r["signal"],
                "str": r["strength"], "price": r["price"],
            })
    st.session_state.alerts    = (alerts + st.session_state.alerts)[:100]
    st.session_state.results   = results
    st.session_state.last_scan = datetime.now()
    st.session_state.scanned   = True
    if failed:
        st.caption(f"⚠️ {len(failed)} tickers failed to download: {', '.join(failed[:10])}{'…' if len(failed)>10 else ''}")

results = st.session_state.results

# ── STATS BAR ─────────────────────────────────────────────────────────────────
if results:
    n_bull = sum(1 for r in results if r["signal"] == "BULL")
    n_bear = sum(1 for r in results if r["signal"] == "BEAR")
    n_vs   = sum(1 for r in results if r["strength"] >= 80)
    n_sig  = sum(1 for r in results if r["signal"] != "NONE")
    avg_s  = np.mean([r["strength"] for r in results if r["signal"] != "NONE"] or [0])
    ls_s   = st.session_state.last_scan.strftime("%H:%M:%S  %d %b") if st.session_state.last_scan else "—"

    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-card" style="--accent:#0891b2;">
        <div class="sc-label">Scanned</div>
        <div class="sc-val">{len(results)}</div>
        <div class="sc-sub">of {len(scan_list)} tickers</div>
      </div>
      <div class="stat-card" style="--accent:#16a34a;">
        <div class="sc-label">↑ Bull Signals</div>
        <div class="sc-val">{n_bull}</div>
        <div class="sc-sub">{n_bull/len(results)*100:.1f}% of universe</div>
      </div>
      <div class="stat-card" style="--accent:#dc2626;">
        <div class="sc-label">↓ Bear Signals</div>
        <div class="sc-val">{n_bear}</div>
        <div class="sc-sub">{n_bear/len(results)*100:.1f}% of universe</div>
      </div>
      <div class="stat-card" style="--accent:#f59e0b;">
        <div class="sc-label">Very Strong ≥80%</div>
        <div class="sc-val">{n_vs}</div>
        <div class="sc-sub">High confidence signals</div>
      </div>
      <div class="stat-card" style="--accent:#7c3aed;">
        <div class="sc-label">Avg Signal Strength</div>
        <div class="sc-val">{avg_s:.1f}%</div>
        <div class="sc-sub">Across {n_sig} active signals</div>
      </div>
      <div class="stat-card" style="--accent:#64748b;">
        <div class="sc-label">Last Scan</div>
        <div class="sc-val" style="font-size:16px;">{ls_s}</div>
        <div class="sc-sub">Auto-refresh every 1 hour</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Alert banner
    if st.session_state.alerts:
        a    = st.session_state.alerts[0]
        bull = a["signal"] == "BULL"
        col  = "#15803d" if bull else "#b91c1c"
        bg   = "#f0fdf4" if bull else "#fef2f2"
        st.markdown(f"""
        <div class="alert-box" style="--alert-col:{col};--alert-bg:{bg};">
          <div>
            <span style="color:{col};font-weight:700;font-size:12px;">
              {'↑' if bull else '↓'} ALERT — {a['ticker']}
            </span>
            <span style="color:#64748b;font-size:10px;margin-left:12px;">
              {a['name']}  ·  Strength {a['str']:.1f}%  ·  ₹{a['price']:,.0f}  ·  {a['ts']}
            </span>
          </div>
          <span style="color:{col};font-size:18px;font-weight:700;">{a['str']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

# ── FILTER + SORT RESULTS ─────────────────────────────────────────────────────
if results:
    rows = list(results)

    if search:
        s = search.upper()
        rows = [r for r in rows if s in r["ticker"] or s in r["name"].upper()]
    if sig_f == "↑ Bull Only":    rows = [r for r in rows if r["signal"] == "BULL"]
    elif sig_f == "↓ Bear Only":  rows = [r for r in rows if r["signal"] == "BEAR"]
    elif sig_f == "Strong ≥80%":  rows = [r for r in rows if r["strength"] >= 80]
    elif sig_f == "Has Signal":   rows = [r for r in rows if r["signal"] != "NONE"]
    if rsi_f == "OB >70":         rows = [r for r in rows if r["rsi"] >= 70]
    elif rsi_f == "OS <30":       rows = [r for r in rows if r["rsi"] <= 30]
    elif rsi_f == "Neutral":      rows = [r for r in rows if 30 < r["rsi"] < 70]

    if sort_f == "Strength ↓":
        rows.sort(key=lambda x: (x["signal"] != "NONE", x["strength"]), reverse=True)
    elif sort_f == "Change % ↓":
        rows.sort(key=lambda x: abs(x["chg"]), reverse=True)
    elif sort_f == "RSI ↓":
        rows.sort(key=lambda x: x["rsi"], reverse=True)
    elif sort_f == "Price ↓":
        rows.sort(key=lambda x: x["price"], reverse=True)
    elif sort_f == "A → Z":
        rows.sort(key=lambda x: x["ticker"])

    # ── TABLE HTML ────────────────────────────────────────────────────────────
    def _chg(v: float) -> str:
        cls = "pos" if v >= 0 else "neg"
        s   = ("+" if v >= 0 else "") + f"{v:.2f}%"
        return f'<span class="{cls}">{s}</span>'

    def _der(v: float, scale: int = 4) -> str:
        cls = "pos" if v > 0 else ("neg" if v < 0 else "neu")
        s   = ("+" if v > 0 else "") + f"{v:.{scale}f}"
        return f'<span class="{cls}">{s}</span>'

    def _rsi(v: float) -> str:
        cls = "rsi-ob" if v >= 70 else ("rsi-os" if v <= 30 else "rsi-n")
        return f'<span class="{cls}">{v:.1f}</span>'

    def _str(v: float, bull: bool) -> str:
        if v == 0:
            return '<span class="neu">—</span>'
        sc = str_col(v, bull)
        return (f'<div class="str-cell">'
                f'<span class="str-num" style="color:{sc};">{v:.1f}%</span>'
                f'<div class="str-track"><div class="str-fill" style="width:{v}%;background:{sc};"></div></div>'
                f'</div>')

    def _rt(v: float) -> str:
        if v == 0: return '<span class="rt-vw">—</span>'
        rt, cls, _ = get_rating(v)
        return f'<span class="{cls}">{rt}</span>'

    def _sig(sig: str) -> str:
        if sig == "BULL": return '<span class="badge b-bull">↑ BULL</span>'
        if sig == "BEAR": return '<span class="badge b-bear">↓ BEAR</span>'
        return '<span class="badge b-none">—</span>'

    tbody = ""
    for r in rows:
        bull = r["signal"] == "BULL"
        bear = r["signal"] == "BEAR"
        rc   = "bull-row" if bull else ("bear-row" if bear else "")
        p_fmt = f"₹{r['price']:,.0f}" if r["price"] >= 100 else f"₹{r['price']:,.2f}"
        tbody += (
            f'<tr class="{rc}">'
            # f'<td><span class="tk" title="{r[chr(34)+"name"+chr(34)]}">{r["ticker"]}</span></td>'
            f'<td>{p_fmt}</td>'
            f'<td>{_chg(r["chg"])}</td>'
            f'<td class="hl-cyan">₹{r["hlc3"]:,.2f}</td>'
            f'<td class="hl-cyan">₹{r["ama"]:,.2f}</td>'
            f'<td class="hl-slate">₹{r["ema70"]:,.2f}</td>'
            f'<td>{_der(r["d1"])}</td>'
            f'<td>{_der(r["d2"], 4)}</td>'
            f'<td>{_der(r["d3"], 2)}</td>'
            f'<td>{_rsi(r["rsi"])}</td>'
            f'<td>{_str(r["strength"], bull)}</td>'
            f'<td>{_rt(r["strength"])}</td>'
            f'<td class="td-sig">{_sig(r["signal"])}</td>'
            f'</tr>'
        )

    st.markdown(f"""
    <div class="tbl-card">
      <div class="tbl-header">
        <span class="tbl-title">NIFTY 500 — GRADIENT SIGNAL SCANNER</span>
        <span class="tbl-count">{len(rows)} results</span>
      </div>
      <div class="tbl-scroll">
        <table class="ama">
          <thead><tr>
            <th>TICKER</th><th>PRICE</th><th>CHG %</th>
            <th>HLC3</th><th>AMA</th><th>EMA70</th>
            <th>f'(x)%</th><th>f''(x)%</th><th>f'''(x)%</th>
            <th>RSI</th><th>STR %</th><th>RATING</th><th class="th-sig">SIGNAL</th>
          </tr></thead>
          <tbody>{tbody}</tbody>
        </table>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    fa, fb, fc = st.columns([4, 1, 1])
    with fa:
        ls_long = st.session_state.last_scan.strftime("%d %b %Y  %H:%M:%S") if st.session_state.last_scan else "—"
        st.markdown(
            f'<div style="font-size:10px;color:#94a3b8;padding-top:6px;">'
            f'{len(rows)} rows shown  ·  {len(results)} tickers scanned  ·  '
            f'Last scan: {ls_long}  ·  Data: Yahoo Finance (yfinance)  ·  '
            f'Not investment advice</div>',
            unsafe_allow_html=True)
    with fb:
        df_out = pd.DataFrame([{
            "Ticker":   r["ticker"], "Name":    r["name"],
            "Price":    round(r["price"], 2), "Chg%":  round(r["chg"], 2),
            "HLC3":     r["hlc3"],  "AMA":     r["ama"],  "EMA70": r["ema70"],
            "f'(x)%":  r["d1"],    "f''(x)%": r["d2"],   "f'''(x)%": r["d3"],
            "RSI":      r["rsi"],   "Str%":    r["strength"],
            "Rating":   get_rating(r["strength"])[0] if r["signal"] != "NONE" else "—",
            "Signal":   r["signal"], "ER":     r["er"],
        } for r in rows])
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button("⬇ Export CSV", df_out.to_csv(index=False),
                           file_name=f"AMA_NIFTY500_{ts}.csv",
                           mime="text/csv", use_container_width=True)
    with fc:
        if st.session_state.alerts:
            with st.expander(f"🔔 Alerts ({len(st.session_state.alerts)})"):
                for a in st.session_state.alerts[:20]:
                    bull_a = a["signal"] == "BULL"
                    col_a  = "#15803d" if bull_a else "#b91c1c"
                    st.markdown(
                        f'<div style="font-size:10px;padding:4px 0;border-bottom:1px solid #f1f5f9;">'
                        f'<span style="color:{col_a};font-weight:600;">{"↑" if bull_a else "↓"} {a["ticker"]}</span>'
                        f'  <span style="color:#94a3b8;">{a["str"]:.1f}%  ·  {a["ts"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;background:#ffffff;
         border:1px solid #e8eaf0;border-radius:12px;margin-top:10px;">
      <div style="font-size:40px;margin-bottom:12px;">⚡</div>
      <div style="font-size:16px;font-weight:600;color:#1a1d2e;margin-bottom:6px;">
        Ready to scan NIFTY 500
      </div>
      <div style="font-size:12px;color:#94a3b8;">
        Click <b style="color:#1a1d2e;">⚡ Scan</b> to fetch all equities via yfinance and run the gradient engine.
      </div>
      <div style="font-size:11px;color:#cbd5e1;margin-top:8px;">
        ~446 tickers  ·  KAMA + f'(x) f''(x) f'''(x)  ·  1-hour cache  ·  EOD data
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#cbd5e1;font-size:9px;letter-spacing:1px;
     border-top:1px solid #e8eaf0;padding:10px 0;margin-top:10px;">
  AMA  ·  GRADIENT BACKPROP ENGINE  ·  NIFTY 500  ·  Yahoo Finance  ·  1-hr refresh  ·  Not investment advice
</div>
""", unsafe_allow_html=True)

# ── AUTO RERUN ─────────────────────────────────────────────────────────────────
if st.session_state.last_scan:
    if int((datetime.now() - st.session_state.last_scan).total_seconds()) >= REFRESH_SECS:
        time.sleep(1)
        st.rerun()
