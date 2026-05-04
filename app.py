"""
AMA — Gradient Backprop + Reversal Strength
NIFTY 500 | Kite API (primary) + yfinance (fallback)

ROOT CAUSE FIX (Kite auth error):
  Two-button flow (Generate + Connect) caused Streamlit rerun between clicks.
  The access token field with value="" was resetting to empty on rerun,
  so "Connect Kite" always received an empty token → "Incorrect api_key or access_token".

  FIX: Single button "Authorise & Connect" — generates session AND connects
  in one click, exactly like the working data.py render_kite_login() pattern.
  request_token is single-use, so it must be consumed in the same execution.

OTHER FIXES:
  1. No @st.cache_resource on kite client  (cached bad connections permanently)
  2. Access token NOT pre-filled from secrets (expires midnight daily)
  3. Disconnect button to clear stale state
  4. OHLC cached with api_key+token keys (no rate-limit hammering)
  5. Notification operator precedence fixed
  6. ltp() key format verified and guarded
  7. IST-aware datetime throughout
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import smtplib
import ssl
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from nifty500 import NIFTY500

IST          = ZoneInfo("Asia/Kolkata")
REFRESH_SECS = 1800   # 30 minutes

st.set_page_config(
    page_title="AMA Gradient — NIFTY 500",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
html,body,[data-testid="stAppViewContainer"],.stApp{background:#f8f9fc!important;font-family:'Inter',sans-serif!important;color:#1a1d2e!important;}
[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stSidebar"]{display:none!important;}
section[data-testid="stSidebar"]{display:none!important;}
.block-container{padding:1rem 1.5rem!important;max-width:100%!important;}
.nav-bar{background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:10px 20px;display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.06);}
.nav-title{font-size:14px;font-weight:700;color:#1a1d2e;letter-spacing:-.3px;}
.nav-sub{font-size:10px;color:#94a3b8;margin-top:1px;letter-spacing:.5px;}
.nav-right{display:flex;align-items:center;gap:14px;}
.nav-badge{display:inline-flex;align-items:center;gap:5px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;color:#16a34a;}
.live-dot{width:6px;height:6px;border-radius:50%;background:#16a34a;animation:blink 1.4s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.nav-time{font-size:11px;color:#64748b;font-family:'JetBrains Mono',monospace;}
.mkt-open{background:#f0fdf4;border:1px solid #bbf7d0;color:#16a34a;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;}
.mkt-close{background:#fef2f2;border:1px solid #fecaca;color:#dc2626;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;}
.box-ok{background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #16a34a;border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px;color:#15803d;}
.box-warn{background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #f59e0b;border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px;color:#92400e;}
.box-err{background:#fef2f2;border:1px solid #fecaca;border-left:4px solid #dc2626;border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px;color:#b91c1c;}
.box-info{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:9px 13px;margin:6px 0;font-size:11px;color:#1e40af;}
.stats-row{display:flex;gap:10px;margin-bottom:10px;}
.stat-card{flex:1;background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:12px 16px;box-shadow:0 1px 4px rgba(0,0,0,.04);}
.sc-label{font-size:10px;font-weight:500;color:#94a3b8;letter-spacing:.8px;text-transform:uppercase;}
.sc-val{font-size:22px;font-weight:700;margin-top:2px;color:var(--accent);}
.sc-sub{font-size:10px;color:#cbd5e1;margin-top:1px;}
.alert-box{border-radius:10px;padding:10px 16px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;border-left:4px solid var(--ac);background:var(--abg);}
.tbl-card{background:#fff;border:1px solid #e8eaf0;border-radius:10px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.05);}
.tbl-hdr{background:#f8f9fc;border-bottom:1px solid #e8eaf0;padding:8px 14px;display:flex;justify-content:space-between;align-items:center;}
.tbl-title{font-size:11px;font-weight:600;color:#475569;letter-spacing:.5px;}
.tbl-cnt{font-size:10px;color:#94a3b8;}
.tbl-scroll{max-height:68vh;overflow-y:auto;}
.tbl-scroll::-webkit-scrollbar{width:4px;}
.tbl-scroll::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:4px;}
table.t{width:100%;border-collapse:collapse;font-size:11px;}
table.t thead th{background:#f8f9fc;color:#64748b;font-size:9px;font-weight:600;letter-spacing:1px;text-transform:uppercase;padding:8px 12px;text-align:right;border-bottom:1px solid #e8eaf0;position:sticky;top:0;z-index:5;white-space:nowrap;}
table.t thead th:first-child{text-align:left;min-width:88px;}
table.t thead th.tc{text-align:center;}
table.t tbody tr{border-bottom:1px solid #f1f5f9;transition:background .1s;}
table.t tbody tr:hover{background:#f8faff;}
table.t tbody tr.br{background:#fafffe;}
table.t tbody tr.rr{background:#fffafa;}
table.t tbody tr.br:hover{background:#f0fdf8;}
table.t tbody tr.rr:hover{background:#fff5f5;}
table.t tbody td{padding:7px 12px;text-align:right;color:#334155;font-family:'JetBrains Mono',monospace;font-size:11px;white-space:nowrap;}
table.t tbody td:first-child{text-align:left;font-family:'Inter',sans-serif;}
table.t tbody td.tc{text-align:center;}
.tk{font-weight:700;color:#1a1d2e;font-size:11px;cursor:default;}
.pos{color:#16a34a;font-weight:600;}.neg{color:#dc2626;font-weight:600;}.neu{color:#64748b;}
.hc{color:#0891b2;font-weight:600;}.hs{color:#475569;}
.badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;font-size:9px;font-weight:700;letter-spacing:.5px;font-family:'Inter',sans-serif;}
.bb{background:#dcfce7;color:#15803d;border:1px solid #bbf7d0;}
.be{background:#fee2e2;color:#b91c1c;border:1px solid #fecaca;}
.bn{background:#f1f5f9;color:#94a3b8;border:1px solid #e2e8f0;}
.bk{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;font-size:8px;}
.by{background:#f5f3ff;color:#6d28d9;border:1px solid #ddd6fe;font-size:8px;}
.sc{display:flex;align-items:center;gap:6px;justify-content:flex-end;}
.st{height:4px;width:44px;background:#e2e8f0;border-radius:3px;flex-shrink:0;}
.sf{height:4px;border-radius:3px;}
.rvs{color:#15803d;font-weight:600;font-size:10px;}.rs{color:#16a34a;font-weight:500;font-size:10px;}
.rm{color:#d97706;font-weight:500;font-size:10px;}.rw{color:#ea580c;font-weight:500;font-size:10px;}
.rvw{color:#94a3b8;font-weight:400;font-size:10px;}
.rsi-ob{color:#dc2626;font-weight:600;}.rsi-os{color:#16a34a;font-weight:600;}.rsi-n{color:#475569;}
.stButton>button{background:#1a1d2e!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:'Inter',sans-serif!important;font-size:12px!important;font-weight:600!important;padding:8px 20px!important;}
.stButton>button:hover{opacity:.85!important;}
.stDownloadButton>button{background:#f1f5f9!important;color:#334155!important;border:1px solid #e2e8f0!important;border-radius:8px!important;font-size:11px!important;}
.stProgress>div>div>div>div{background:#2d3561!important;border-radius:4px!important;}
label[data-testid="stWidgetLabel"]{font-size:11px!important;color:#64748b!important;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# KITE API LAYER
# ══════════════════════════════════════════════════════════════════════════════

def kite_login_url(api_key: str) -> str:
    api_key = (api_key or "").strip()
    if not api_key:
        return "#"
    try:
        from kiteconnect import KiteConnect
        return KiteConnect(api_key=api_key).login_url()
    except Exception:
        return f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"


def authorise_and_connect(api_key: str, api_secret: str, request_token: str):
    """
    *** KEY FIX ***
    Single-step: generate_session + validate profile in ONE execution.
    Mirrors exactly how data.py works (the project that IS connecting correctly).

    request_token is single-use — must be consumed immediately, not across reruns.
    Returns (access_token, kite_obj, username, error_str).
    """
    api_key       = (api_key or "").strip()
    api_secret    = (api_secret or "").strip()
    request_token = (request_token or "").strip()

    if not api_key:
        return "", None, "", "API Key is empty"
    if not api_secret:
        return "", None, "", "API Secret is empty"
    if not request_token:
        return "", None, "", "request_token is empty — complete Step 1 first"

    try:
        from kiteconnect import KiteConnect
    except ImportError:
        return "", None, "", "kiteconnect not installed — add it to requirements.txt"

    try:
        kite     = KiteConnect(api_key=api_key)
        session  = kite.generate_session(request_token, api_secret=api_secret)
        access_token = session["access_token"]
        kite.set_access_token(access_token)
        profile  = kite.profile()
        username = profile.get("user_name", "User")
        return access_token, kite, username, ""
    except Exception as e:
        msg = str(e)
        if "token" in msg.lower() or "api_key" in msg.lower() or "incorrect" in msg.lower():
            msg = (
                "Token error — most common causes:\n"
                "• request_token already used (each token works ONCE only — "
                "re-login to get a fresh one)\n"
                "• Access token expired (resets every midnight IST)\n"
                "• API Key mismatch with the app that generated the request_token\n"
                f"Original error: {msg}"
            )
        return "", None, "", msg


def connect_with_access_token(api_key: str, access_token: str):
    """
    Connect using a pre-generated access token (stored in session/secrets).
    Returns (kite_obj, username, error_str).
    """
    api_key      = (api_key or "").strip()
    access_token = (access_token or "").strip()
    if not api_key or not access_token:
        return None, "", "API Key or Access Token is empty"
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        profile = kite.profile()
        return kite, profile.get("user_name", "User"), ""
    except Exception as e:
        return None, "", str(e)


# FIX 4: Cache instruments keyed on access_token (24 hr TTL)
@st.cache_data(ttl=86400, show_spinner=False)
def load_instruments(api_key: str, access_token: str) -> dict:
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key.strip())
        kite.set_access_token(access_token.strip())
        inst = kite.instruments("NSE")
        return {i["tradingsymbol"]: i["instrument_token"]
                for i in inst if i["segment"] == "NSE"}
    except Exception:
        return {}


# FIX 4: Cache OHLC keyed on access_token+ticker (30 min TTL)
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_kite_ohlc(api_key: str, access_token: str,
                    instrument_token: int, interval: str, days_back: int):
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key.strip())
        kite.set_access_token(access_token.strip())
        data = kite.historical_data(
            instrument_token,
            from_date=date.today() - timedelta(days=days_back),
            to_date=date.today(),
            interval=interval,
        )
        if not data:
            return None
        df = pd.DataFrame(data)
        df.columns = [c.capitalize() for c in df.columns]
        df = df.dropna(subset=["Close"])
        return df if len(df) > 20 else None
    except Exception:
        return None


# FIX 6: ltp() uses "NSE:SYMBOL" — correct format, fully guarded
def get_live_price(api_key: str, access_token: str, ticker: str):
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key.strip())
        kite.set_access_token(access_token.strip())
        key = f"NSE:{ticker}"
        q   = kite.ltp([key])
        if q and key in q:
            return float(q[key]["last_price"])
    except Exception:
        pass
    return None


# ── yfinance fallback ──────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_yf(ticker: str, period: str, interval: str):
    try:
        import yfinance as yf
        df = yf.download(f"{ticker}.NS", period=period, interval=interval,
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"])
        return df if len(df) > 20 else None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# MATH ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def calc_kama(hlc3: np.ndarray, er_len=10, fast=6, slow=7) -> np.ndarray:
    fsc, ssc = 2.0/(fast+1), 2.0/(slow+1)
    n  = len(hlc3)
    ama = np.empty(n); ama[0] = hlc3[0]
    for i in range(1, n):
        if i < er_len:
            ama[i] = hlc3[i]; continue
        d  = abs(hlc3[i] - hlc3[i-er_len])
        v  = np.sum(np.abs(np.diff(hlc3[i-er_len:i+1])))
        er = d/v if v else 0.0
        sc = (er*(fsc-ssc)+ssc)**2
        ama[i] = ama[i-1] + sc*(hlc3[i]-ama[i-1])
    return ama


def calc_rsi(close: np.ndarray, period=14) -> float:
    if len(close) < period+1:
        return 50.0
    d  = np.diff(close[-(period+2):])
    ag = np.mean(np.where(d>0, d, 0.0)[-period:])
    al = np.mean(np.where(d<0, -d, 0.0)[-period:])
    return round(100.0 if al==0 else 100-100/(1+ag/al), 1)


def compute_signal(hlc3: np.ndarray, close: np.ndarray, p: dict) -> dict:
    ama = calc_kama(hlc3, p["er_len"], p["fast"], p["slow"])
    ema = float(pd.Series(close).ewm(span=p["ema_len"], adjust=False).mean().iloc[-1])
    rsi = calc_rsi(close, 14)
    n   = len(ama)
    d1  = np.zeros(n); d2 = np.zeros(n); d3 = np.zeros(n)
    for i in range(1, n):
        if ama[i]: d1[i] = (ama[i]-ama[i-1])/ama[i]*100
    for i in range(2, n):
        if ama[i]: d2[i] = (d1[i]-d1[i-1])/ama[i]*1e4
    for i in range(3, n):
        if ama[i]: d3[i] = (d2[i]-d2[i-1])/ama[i]*1e6
    el = p["er_len"]
    er_v = 0.0
    if n > el:
        dd = abs(hlc3[-1]-hlc3[-1-el])
        vv = np.sum(np.abs(np.diff(hlc3[-1-el:])))
        er_v = dd/vv if vv else 0.0
    d1v, d2v, d3v = d1[-1], d2[-1], d3[-1]
    gfb = (d2v>0 and d1v<0) or (d3v>0 and d2v<0 and d1v<0)
    gfr = (d2v<0 and d1v>0) or (d3v<0 and d2v>0 and d1v>0)
    strength = 0.0; boost = False
    c1 = c2 = c3 = raw = mx = 0.0
    if gfb or gfr:
        c1  = abs(d2v); c2 = abs(d1v)*abs(d2v); c3 = abs(d3v)*0.1
        raw = c1*p["wa"] + c2*p["wb"] + c3*p["wc"]
        lb  = max(0, n-1-p["lookback"])
        mA  = np.max(np.abs(d2[lb:]))
        mD  = np.max(np.abs(d1[lb:])*np.abs(d2[lb:]))
        mJ  = np.max(np.abs(d3[lb:])*0.1)
        mx  = max(1e-9, mA*p["wa"]+mD*p["wb"]+mJ*p["wc"])
        strength = min(100.0, raw/mx*100)
        if abs(d1v)>p["bd1"] and abs(d2v)>p["bd2"]:
            strength = min(100.0, strength*1.25); boost = True
    sig = "NONE"
    if p["filt"]:
        if gfb and strength>=p["min_str"]:   sig = "BULL"
        elif gfr and strength>=p["min_str"]: sig = "BEAR"
    else:
        if gfb:  sig = "BULL"
        elif gfr: sig = "BEAR"
    return dict(hlc3=round(float(hlc3[-1]),2), ama=round(float(ama[-1]),2),
                ema70=round(ema,2), d1=round(d1v,4), d2=round(d2v,6),
                d3=round(d3v,4), rsi=rsi, strength=round(strength,1),
                signal=sig, gf_bull=gfb, gf_bear=gfr, boost=boost, er=round(er_v,4))


def get_rating(s: float):
    if s>=80: return "VERY STRONG","rvs","#15803d"
    if s>=60: return "STRONG",     "rs", "#16a34a"
    if s>=40: return "MODERATE",   "rm", "#d97706"
    if s>=20: return "WEAK",       "rw", "#ea580c"
    return "VERY WEAK","rvw","#94a3b8"


def scol(s: float, bull: bool) -> str:
    if s>=80: return "#15803d" if bull else "#b91c1c"
    if s>=60: return "#16a34a" if bull else "#dc2626"
    if s>=40: return "#d97706"
    return "#ea580c"


# ══════════════════════════════════════════════════════════════════════════════
# PROCESS TICKER  (Kite → yfinance fallback)
# ══════════════════════════════════════════════════════════════════════════════
def process_ticker(ticker: str, p: dict,
                   api_key: str = "", access_token: str = "",
                   instruments: dict = None) -> dict | None:
    df  = None
    src = "yf"
    if api_key and access_token and instruments:
        token = instruments.get(ticker)
        if token:
            ki   = p.get("kite_interval", "day")
            days = {"minute":5,"5minute":30,"15minute":60,"60minute":90,"day":90}.get(ki,90)
            df   = fetch_kite_ohlc(api_key, access_token, int(token), ki, days)
            if df is not None:
                src = "kite"
    if df is None:
        df = fetch_yf(ticker, p["period"], p["interval"])
    if df is None:
        return None
    try:
        h    = df["High"].values.astype(float)
        l    = df["Low"].values.astype(float)
        c    = df["Close"].values.astype(float)
        hlc3 = (h+l+c)/3
        if len(hlc3) < p["er_len"]+5:
            return None
        sig   = compute_signal(hlc3, c, p)
        price = float(c[-1])
        prev  = float(c[-2]) if len(c)>1 else price
        if src=="kite" and api_key and access_token:
            live = get_live_price(api_key, access_token, ticker)
            if live:
                price = live
        return dict(ticker=ticker, name=NIFTY500.get(ticker, ticker),
                    price=price, prev=prev,
                    chg=(price-prev)/prev*100 if prev else 0.0,
                    src=src, **sig)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# ALERT FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def _push_body(alerts: list, scan_time: str):
    bull  = [a for a in alerts if a["signal"]=="BULL"]
    bear  = [a for a in alerts if a["signal"]=="BEAR"]
    title = f"AMA NIFTY500 | {len(bull)} BULL {len(bear)} BEAR | {scan_time} IST"
    lines = [f"VERY STRONG signals at {scan_time} IST"]
    if bull: lines.append("BULL: "+", ".join(f"{a['ticker']}({a['str']:.0f}%)" for a in bull[:6]))
    if bear: lines.append("BEAR: "+", ".join(f"{a['ticker']}({a['str']:.0f}%)" for a in bear[:6]))
    if len(alerts)>12: lines.append(f"...and {len(alerts)-12} more")
    return title, "\n".join(lines)


def send_ntfy(topic: str, alerts: list, scan_time: str):
    if not topic or not alerts: return False, "No topic or no alerts"
    topic = topic.strip().replace(" ","-")
    title, body = _push_body(alerts, scan_time)
    try:
        import requests as _r
        r = _r.post(f"https://ntfy.sh/{topic}", data=body.encode(),
                    headers={"Title":title,"Priority":"high","Tags":"bell",
                             "Content-Type":"text/plain"}, timeout=12)
        return (True, f"Push sent to '{topic}'") if r.status_code==200 \
               else (False, f"ntfy HTTP {r.status_code}: {r.text[:80]}")
    except Exception as e:
        return False, f"ntfy error: {str(e)[:80]}"


def send_telegram(token: str, chat_id: str, alerts: list, scan_time: str):
    if not token or not chat_id or not alerts: return False, "Missing credentials"
    title, body = _push_body(alerts, scan_time)
    try:
        import requests as _r
        r = _r.post(f"https://api.telegram.org/bot{token.strip()}/sendMessage",
                    json={"chat_id":chat_id.strip(),
                          "text":f"*{title}*\n\n{body}","parse_mode":"Markdown"},
                    timeout=12)
        if r.status_code==200: return True, f"Telegram sent to {chat_id}"
        return False, f"Telegram: {r.json().get('description', r.text[:60])}"
    except Exception as e:
        return False, f"Telegram error: {str(e)[:80]}"


def build_email_html(alerts: list, scan_time: str, thr: int) -> str:
    br = [a for a in alerts if a["signal"]=="BULL"]
    be = [a for a in alerts if a["signal"]=="BEAR"]
    def rows(items, col, lbl):
        if not items:
            return (f'<tr><td colspan="4" style="padding:10px;color:#94a3b8;'
                    f'text-align:center;">No {lbl} signals</td></tr>')
        out = ""
        for a in items:
            bg = "#dcfce7" if lbl=="BULL" else "#fee2e2"
            out += (f'<tr style="border-bottom:1px solid #f1f5f9;">'
                    f'<td style="padding:7px 12px;font-weight:700;color:#1a1d2e;">{a["ticker"]}</td>'
                    f'<td style="padding:7px 12px;text-align:right;">Rs.{a["price"]:,.0f}</td>'
                    f'<td style="padding:7px 12px;text-align:right;font-weight:700;'
                    f'color:{col};">{a["str"]:.1f}%</td>'
                    f'<td style="padding:7px 12px;text-align:center;">'
                    f'<span style="background:{bg};color:{col};border-radius:12px;'
                    f'padding:2px 8px;font-size:10px;font-weight:700;">{lbl}</span></td></tr>')
        return out
    return (f'<html><body style="font-family:Inter,sans-serif;background:#f8f9fc;'
            f'margin:0;padding:20px;"><div style="max-width:640px;margin:0 auto;">'
            f'<div style="background:#1a1d2e;border-radius:10px 10px 0 0;padding:16px 20px;">'
            f'<div style="color:#f59e0b;font-size:16px;font-weight:700;">AMA Gradient Signal Alert</div>'
            f'<div style="color:#94a3b8;font-size:11px;margin-top:3px;">'
            f'NIFTY 500 | {scan_time} IST | Threshold: >={thr}%</div></div>'
            f'<div style="background:#fff;padding:12px 20px;display:flex;gap:10px;'
            f'border-bottom:1px solid #e8eaf0;">'
            f'<div style="background:#dcfce7;border-radius:8px;padding:8px 14px;text-align:center;">'
            f'<div style="font-size:18px;font-weight:700;color:#15803d;">{len(br)}</div>'
            f'<div style="font-size:9px;color:#16a34a;font-weight:600;">BULL</div></div>'
            f'<div style="background:#fee2e2;border-radius:8px;padding:8px 14px;text-align:center;">'
            f'<div style="font-size:18px;font-weight:700;color:#b91c1c;">{len(be)}</div>'
            f'<div style="font-size:9px;color:#dc2626;font-weight:600;">BEAR</div></div></div>'
            f'<div style="background:#fff;">'
            f'<div style="padding:7px 20px;background:#f0fdf4;border-bottom:1px solid #bbf7d0;">'
            f'<span style="font-size:11px;font-weight:700;color:#15803d;">BULLISH REVERSALS</span></div>'
            f'<table style="width:100%;border-collapse:collapse;font-size:12px;">'
            f'<thead><tr style="background:#f8f9fc;">'
            f'<th style="padding:6px 12px;text-align:left;color:#64748b;font-size:9px;">TICKER</th>'
            f'<th style="padding:6px 12px;text-align:right;color:#64748b;font-size:9px;">PRICE</th>'
            f'<th style="padding:6px 12px;text-align:right;color:#64748b;font-size:9px;">STR%</th>'
            f'<th style="padding:6px 12px;text-align:center;color:#64748b;font-size:9px;">SIGNAL</th>'
            f'</tr></thead><tbody>{rows(br,"#15803d","BULL")}</tbody></table></div>'
            f'<div style="background:#fff;margin-top:1px;">'
            f'<div style="padding:7px 20px;background:#fef2f2;border-bottom:1px solid #fecaca;">'
            f'<span style="font-size:11px;font-weight:700;color:#b91c1c;">BEARISH REVERSALS</span></div>'
            f'<table style="width:100%;border-collapse:collapse;font-size:12px;">'
            f'<thead><tr style="background:#f8f9fc;">'
            f'<th style="padding:6px 12px;text-align:left;color:#64748b;font-size:9px;">TICKER</th>'
            f'<th style="padding:6px 12px;text-align:right;color:#64748b;font-size:9px;">PRICE</th>'
            f'<th style="padding:6px 12px;text-align:right;color:#64748b;font-size:9px;">STR%</th>'
            f'<th style="padding:6px 12px;text-align:center;color:#64748b;font-size:9px;">SIGNAL</th>'
            f'</tr></thead><tbody>{rows(be,"#b91c1c","BEAR")}</tbody></table></div>'
            f'<div style="background:#f8f9fc;border-radius:0 0 10px 10px;padding:10px 20px;'
            f'border-top:1px solid #e8eaf0;text-align:center;">'
            f'<p style="font-size:10px;color:#94a3b8;margin:0;">'
            f'AMA Gradient Backprop | NIFTY 500 | Not investment advice.</p>'
            f'</div></div></body></html>')


def send_email(sender: str, password: str, recipient: str,
               alerts: list, scan_time: str, thr: int):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"AMA Alert — {len(alerts)} signals >={thr}% [{scan_time}]"
        msg["From"] = sender; msg["To"] = recipient
        msg.attach(MIMEText(build_email_html(alerts, scan_time, thr), "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())
        return True, f"Email sent to {recipient}"
    except smtplib.SMTPAuthenticationError:
        return False, "Auth failed — use Gmail App Password, not regular password"
    except Exception as e:
        return False, f"Email error: {str(e)[:80]}"


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE + SECRETS
# FIX 2: kite_access_token NOT loaded from secrets (expires midnight daily)
# ══════════════════════════════════════════════════════════════════════════════
_SS_DEF = {
    "results": [], "alerts": [], "last_scan": None,
    "scanned": False, "email_log": [],
    "kite_connected": False, "kite_user": "", "kite_err": "",
    "kite_ak": "", "kite_at": "",
    "instruments": {},
}
for k, v in _SS_DEF.items():
    if k not in st.session_state:
        st.session_state[k] = v

_SEC = st.secrets if hasattr(st, "secrets") else {}
def _sec(key, default=""):
    try:    return str(_SEC.get(key, default) or default)
    except: return default

# Pre-populate from secrets — API Key & Secret (permanent), NOT access_token
_SK = {
    "kite_api_key":    _sec("kite_api_key"),
    "kite_api_secret": _sec("kite_api_secret"),
    # access_token intentionally excluded — expires at midnight
    "ntfy_topic":      _sec("ntfy_topic"),
    "ntfy_enabled":    _sec("ntfy_enabled","false").lower()=="true",
    "tg_token":        _sec("tg_token"),
    "tg_chat_id":      _sec("tg_chat_id"),
    "tg_enabled":      _sec("tg_enabled","false").lower()=="true",
    "gmail_sender":    _sec("gmail_sender"),
    "gmail_password":  _sec("gmail_password"),
    "gmail_recipient": _sec("gmail_recipient"),
    "email_enabled":   _sec("email_enabled","false").lower()=="true",
}
for k, v in _SK.items():
    if k not in st.session_state:
        st.session_state[k] = v

def gcred(key):
    s = _sec(key)
    return s if s else str(st.session_state.get(key,"") or "")

params = dict(er_len=10, fast=6, slow=7, ema_len=70, lookback=20,
              min_str=50, filt=True, wa=0.35, wb=0.012, wc=0.50,
              bd1=1.0, bd2=0.5, period="3mo", interval="1d", kite_interval="day")


# ══════════════════════════════════════════════════════════════════════════════
# NAV BAR
# ══════════════════════════════════════════════════════════════════════════════
now   = datetime.now(IST)
_m    = now.hour*60 + now.minute
mkt   = now.weekday()<5 and 9*60+15 <= _m <= 15*60+30
mkt_h = ('<span class="mkt-open">● NSE OPEN</span>' if mkt
         else '<span class="mkt-close">● NSE CLOSED</span>')
ls      = st.session_state.last_scan
elapsed = int((now-ls).total_seconds()) if ls is not None else REFRESH_SECS+1
rem     = max(0, REFRESH_SECS-elapsed)
nxt     = f"Next scan {rem//60:02d}:{rem%60:02d}" if ls else ""
ksrc    = "Kite API" if st.session_state.kite_connected else "yfinance fallback"

st.markdown(f"""
<div class="nav-bar">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:32px;height:32px;border-radius:8px;
         background:linear-gradient(135deg,#1a1d2e,#2d3561);
         display:flex;align-items:center;justify-content:center;
         font-size:14px;color:#f59e0b;font-weight:700;">⚡</div>
    <div>
      <div class="nav-title">AMA v3.0 — Gradient Backprop + Reversal Strength</div>
      <div class="nav-sub">NIFTY 500  ·  KAMA  ·  f'(x) f''(x) f'''(x)  ·  {ksrc}  ·  {nxt}</div>
    </div>
  </div>
  <div class="nav-right">
    <div class="nav-badge"><span class="live-dot"></span>LIVE</div>
    <span class="nav-time">{now.strftime('%H:%M:%S  %d %b %Y IST')}</span>
    {mkt_h}
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# KITE API PANEL  ← ROOT CAUSE FIX IS HERE
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🔑  Zerodha Kite API Setup", expanded=not st.session_state.kite_connected):

    # Status banner
    if st.session_state.kite_connected:
        st.markdown(
            f'<div class="box-ok">✅ Connected as <b>{st.session_state.kite_user}</b>  ·  '
            f'{len(st.session_state.instruments):,} NSE instruments loaded</div>',
            unsafe_allow_html=True)
    elif st.session_state.kite_err:
        for line in st.session_state.kite_err.split("\n"):
            if line.strip():
                st.markdown(f'<div class="box-err">❌ {line}</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="box-warn">⚠️ Not connected — using yfinance (EOD data only)</div>',
            unsafe_allow_html=True)

    # ── How-to box ────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="box-info">
    <b>One-time setup:</b>
    <a href="https://developers.kite.trade" target="_blank" style="color:#1d4ed8;">
    developers.kite.trade</a> → My Apps → Create App → copy <b>API Key</b> and <b>API Secret</b>.
    Set Redirect URL to your Streamlit app URL (or <code>https://127.0.0.1</code>).<br><br>
    <b>Every trading day</b> (access token resets at midnight IST):<br>
    &nbsp; <b>Step 1</b> — Enter API Key + Secret → click the <b>Login to Kite ↗</b> link → approve on Zerodha<br>
    &nbsp; <b>Step 2</b> — Copy the <code>request_token</code> from the URL you are redirected to<br>
    &nbsp; <b>Step 3</b> — Paste it below → click <b>Authorise &amp; Connect</b> (one click does everything)
    </div>
    """, unsafe_allow_html=True)

    # ── Credential inputs ─────────────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        api_key_in = st.text_input(
            "Kite API Key",
            value=gcred("kite_api_key"),
            placeholder="e.g. abc123xyz456",
            key="kite_api_key",
        )
    with c2:
        api_secret_in = st.text_input(
            "Kite API Secret",
            value=gcred("kite_api_secret"),
            type="password",
            placeholder="your_api_secret",
            key="kite_api_secret",
        )

    # Login link — shown as soon as API key is entered
    if api_key_in:
        login_url = kite_login_url(api_key_in)
        st.markdown(
            f'<div class="box-ok" style="margin:6px 0;">'
            f'<b>Step 1:</b> '
            f'<a href="{login_url}" target="_blank" style="color:#1d4ed8;font-weight:700;">'
            f'Login to Kite ↗</a>'
            f' → approve → copy the <code>request_token</code> value from the redirect URL'
            f'</div>',
            unsafe_allow_html=True)
    else:
        st.info("Enter your API Key above to get the Kite login link.")

    # request_token + single action button (THE FIX)
    ra, rb, rc = st.columns([3, 1, 1])
    with ra:
        req_tok = st.text_input(
            "Step 2 — Paste request_token from redirect URL",
            placeholder="e.g. K3xyz789abc... (from the URL after Kite login)",
            key="req_token_field",
        )
    with rb:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        # *** THE FIX: single button = generate_session + connect in ONE execution ***
        # request_token is single-use; consuming it across two separate button-click
        # reruns was the root cause of "Incorrect api_key or access_token".
        if st.button("✅ Authorise & Connect", use_container_width=True, key="btn_auth_connect"):
            ak  = (api_key_in or "").strip()
            aks = (api_secret_in or "").strip()
            rt  = (req_tok or "").strip()
            if not ak:
                st.warning("Enter your API Key first.")
            elif not aks:
                st.warning("Enter your API Secret first.")
            elif not rt:
                st.warning("Paste the request_token from the redirect URL (Step 2).")
            else:
                with st.spinner("Authorising with Zerodha and connecting…"):
                    access_token, kite_obj, uname, err = authorise_and_connect(ak, aks, rt)
                if kite_obj:
                    st.session_state.kite_connected = True
                    st.session_state.kite_user      = uname
                    st.session_state.kite_err       = ""
                    st.session_state.kite_ak        = ak
                    st.session_state.kite_at        = access_token
                    with st.spinner("Loading NSE instruments…"):
                        st.session_state.instruments = load_instruments(ak, access_token)
                    st.success(
                        f"✅ Connected as {uname}  ·  "
                        f"{len(st.session_state.instruments):,} instruments loaded")
                    st.rerun()
                else:
                    st.session_state.kite_connected = False
                    st.session_state.kite_err       = err
                    st.rerun()
    with rc:
        # Disconnect / Reset
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Disconnect", use_container_width=True, key="btn_disconnect"):
            st.session_state.kite_connected = False
            st.session_state.kite_user      = ""
            st.session_state.kite_err       = ""
            st.session_state.kite_ak        = ""
            st.session_state.kite_at        = ""
            st.session_state.instruments    = {}
            try: fetch_kite_ohlc.clear()
            except: pass
            try: load_instruments.clear()
            except: pass
            st.rerun()

    st.markdown("""
    <div style="font-size:10px;color:#94a3b8;margin-top:6px;">
    💡 Save <code>kite_api_key</code> and <code>kite_api_secret</code> in
    Streamlit Secrets (Settings → Secrets) — permanent.
    Do <b>NOT</b> save access_token — it expires every midnight IST.
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ALERT SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🔔  Alert Settings  —  Gmail + Mobile Push", expanded=False):
    tab_push, tab_mail = st.tabs(["📱 Mobile Push (ntfy / Telegram)", "📧 Gmail"])
    _sample = [{"ticker":"RELIANCE","signal":"BULL","str":91.2,"price":2950.0},
               {"ticker":"TCS","signal":"BEAR","str":84.7,"price":4120.0}]

    with tab_push:
        method = st.radio("Push method", ["ntfy.sh","Telegram Bot"],
                          horizontal=True, key="push_method")
        if method == "ntfy.sh":
            st.markdown("""<div class="box-info">Install <b>ntfy</b> app (Android/iOS) →
            tap + → subscribe to your topic name. Use hyphens only, no underscores.
            e.g. <code>ama-nifty-raj2024</code></div>""", unsafe_allow_html=True)
            n1, n2 = st.columns([3,1])
            with n1:
                st.text_input("ntfy topic (hyphens only)",
                              value=gcred("ntfy_topic"),
                              placeholder="ama-nifty-yourname-2024", key="ntfy_topic")
            with n2:
                st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
                st.toggle("Enable ntfy",
                          value=bool(st.session_state.get("ntfy_enabled")), key="ntfy_enabled")
                if st.button("Test ntfy", use_container_width=True, key="btn_ntfy"):
                    t = st.session_state.get("ntfy_topic","")
                    if t:
                        with st.spinner("Sending…"):
                            ok, msg = send_ntfy(t, _sample, now.strftime("%H:%M"))
                        st.success(msg) if ok else st.error(msg)
                    else: st.warning("Enter topic first.")
        else:
            st.markdown("""<div class="box-info">
            @BotFather → /newbot → copy token. Message your bot →
            visit api.telegram.org/bot&lt;TOKEN&gt;/getUpdates → copy the id number.
            </div>""", unsafe_allow_html=True)
            t1, t2, t3 = st.columns([3,2,1])
            with t1:
                st.text_input("Bot Token", value=gcred("tg_token"), type="password",
                              placeholder="123456:ABCdef…", key="tg_token")
            with t2:
                st.text_input("Chat ID", value=gcred("tg_chat_id"),
                              placeholder="123456789", key="tg_chat_id")
            with t3:
                st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
                st.toggle("Enable Telegram",
                          value=bool(st.session_state.get("tg_enabled")), key="tg_enabled")
                if st.button("Test", use_container_width=True, key="btn_tg"):
                    tok = st.session_state.get("tg_token","")
                    cid = st.session_state.get("tg_chat_id","")
                    if tok and cid:
                        with st.spinner("Sending…"):
                            ok, msg = send_telegram(tok, cid, _sample, now.strftime("%H:%M"))
                        st.success(msg) if ok else st.error(msg)
                    else: st.warning("Enter token and chat ID first.")

    with tab_mail:
        m1, m2, m3 = st.columns([2,2,1])
        with m1:
            st.text_input("Gmail sender", value=gcred("gmail_sender"),
                          placeholder="you@gmail.com", key="gmail_sender")
            st.text_input("App Password", value=gcred("gmail_password"),
                          type="password", placeholder="abcd efgh ijkl mnop",
                          key="gmail_password")
        with m2:
            st.text_input("Recipient", value=gcred("gmail_recipient"),
                          placeholder="recipient@gmail.com", key="gmail_recipient")
            st.slider("Threshold %", 50, 100, 80, 5, key="alert_threshold")
        with m3:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            st.toggle("Enable email",
                      value=bool(st.session_state.get("email_enabled")), key="email_enabled")
            if st.button("Test Email", use_container_width=True, key="btn_email"):
                s=gcred("gmail_sender"); p=gcred("gmail_password"); r=gcred("gmail_recipient")
                if s and p and r:
                    with st.spinner("Sending…"):
                        ok, msg = send_email(s.strip(), p.replace(" ",""), r.strip(),
                            [{"ticker":"RELIANCE","name":"Reliance Industries",
                              "signal":"BULL","str":87.5,"price":2950.0}],
                            now.strftime("%H:%M:%S"), 80)
                    st.success(msg) if ok else st.error(msg)
                else: st.warning("Fill all email fields first.")
        if st.session_state.email_log:
            st.caption("  ·  ".join(st.session_state.email_log[-5:]))


# ══════════════════════════════════════════════════════════════════════════════
# CONTROLS ROW
# ══════════════════════════════════════════════════════════════════════════════
c1,c2,c3,c4,c5,c6,c7,c8,c9 = st.columns([2.5,1.4,1.4,1.4,1.1,1.1,1.1,1,1])
with c1: search   = st.text_input("","",placeholder="🔍 Search ticker…",
                                  label_visibility="collapsed")
with c2: universe = st.selectbox("",["NIFTY 500","NIFTY 50","NIFTY Next 50","Custom"],
                                 label_visibility="collapsed")
with c3: sig_f    = st.selectbox("",["All","↑ Bull","↓ Bear","Strong >=80%","Has Signal"],
                                 label_visibility="collapsed")
with c4: sort_f   = st.selectbox("",["Strength ↓","Change % ↓","RSI ↓","Price ↓","A→Z"],
                                 label_visibility="collapsed")
with c5: rsi_f    = st.selectbox("",["RSI: All","OB >70","OS <30","Neutral"],
                                 label_visibility="collapsed")
with c6:
    period = st.selectbox("",["3mo","6mo","1y","2y"], label_visibility="collapsed")
    params["period"] = period
with c7:
    if st.session_state.kite_connected:
        ki = st.selectbox("",["day","60minute","15minute","5minute","minute"],
                          label_visibility="collapsed", key="ki_sel")
        params["kite_interval"] = ki
    else:
        st.markdown(
            "<div style='height:38px;font-size:9px;color:#94a3b8;padding-top:10px;'>"
            "yfinance mode</div>", unsafe_allow_html=True)
with c8:
    mui = st.selectbox("",["Min 50%","Min 60%","Min 70%","Min 80%","No Filter"],
                       label_visibility="collapsed", key="min_str_sel")
    _mm = {"Min 50%":50,"Min 60%":60,"Min 70%":70,"Min 80%":80,"No Filter":0}
    params["min_str"] = _mm[mui]; params["filt"] = params["min_str"]>0
with c9:
    run_btn = st.button("⚡  Scan", use_container_width=True)

tickers_all = list(NIFTY500.keys())
if universe == "NIFTY 50":
    scan_list = tickers_all[:50]
elif universe == "NIFTY Next 50":
    scan_list = tickers_all[50:100]
elif universe == "Custom":
    scan_list = st.multiselect("Tickers:", tickers_all,
        default=["RELIANCE","TCS","INFY","HDFCBANK","SBIN"])
    if not scan_list: scan_list = tickers_all[:50]
else:
    scan_list = tickers_all

# Auto-refresh (market hours only)
if mkt and elapsed >= REFRESH_SECS: run_btn = True
if not st.session_state.scanned:    run_btn = True


# ══════════════════════════════════════════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════════════════════════════════════════
if run_btn:
    prog = st.progress(0, text="Starting scan…")
    results, failed = [], []
    ak  = st.session_state.kite_ak
    at  = st.session_state.kite_at
    ins = st.session_state.instruments

    for idx, tk in enumerate(scan_list):
        src_lbl = "[KITE]" if (ak and at and ins.get(tk)) else "[YF]"
        prog.progress((idx+1)/len(scan_list),
                      text=f"{src_lbl} {tk}  ({idx+1}/{len(scan_list)})")
        r = process_ticker(tk, params, ak, at, ins)
        if r:  results.append(r)
        else:  failed.append(tk)
    prog.empty()

    scan_time = datetime.now(IST).strftime("%H:%M:%S")
    thr       = 80
    new_alerts = [
        dict(ts=scan_time, ticker=r["ticker"], name=r["name"],
             signal=r["signal"], str=r["strength"], price=r["price"])
        for r in results
        if r["signal"] != "NONE" and r["strength"] >= thr
    ]
    st.session_state.alerts    = (new_alerts + st.session_state.alerts)[:100]
    st.session_state.results   = results
    st.session_state.last_scan = datetime.now(IST)
    st.session_state.scanned   = True

    # FIX 5: Each notification channel checked independently
    if new_alerts:
        email_on = (gcred("email_enabled")=="True"
                    or bool(st.session_state.get("email_enabled")))
        if email_on and gcred("gmail_sender") and gcred("gmail_password") and gcred("gmail_recipient"):
            ok, msg = send_email(gcred("gmail_sender").strip(),
                                 gcred("gmail_password").replace(" ",""),
                                 gcred("gmail_recipient").strip(),
                                 new_alerts, scan_time, thr)
            st.session_state.email_log = (
                [f"{scan_time}: {'OK' if ok else 'FAIL'} email — {msg}"]
                + st.session_state.email_log)[:10]

        ntfy_on = (gcred("ntfy_enabled")=="True"
                   or bool(st.session_state.get("ntfy_enabled")))
        if ntfy_on and gcred("ntfy_topic").strip():
            ok, msg = send_ntfy(gcred("ntfy_topic"), new_alerts, scan_time)
            st.session_state.email_log = (
                [f"{scan_time}: {'OK' if ok else 'FAIL'} ntfy — {msg}"]
                + st.session_state.email_log)[:10]

        tg_on = (gcred("tg_enabled")=="True"
                 or bool(st.session_state.get("tg_enabled")))
        if tg_on and gcred("tg_token").strip() and gcred("tg_chat_id").strip():
            ok, msg = send_telegram(gcred("tg_token"), gcred("tg_chat_id"),
                                    new_alerts, scan_time)
            st.session_state.email_log = (
                [f"{scan_time}: {'OK' if ok else 'FAIL'} telegram — {msg}"]
                + st.session_state.email_log)[:10]

    kn    = sum(1 for r in results if r.get("src")=="kite")
    parts = [f"✅ {len(results)} tickers scanned"]
    if ak: parts.append(f"Kite:{kn}  yf:{len(results)-kn}")
    if new_alerts: parts.append(f"🔔 {len(new_alerts)} alerts fired")
    if failed:     parts.append(f"⚠️ {len(failed)} failed")
    st.caption("  ·  ".join(parts))

results = st.session_state.results


# ══════════════════════════════════════════════════════════════════════════════
# STATS BAR
# ══════════════════════════════════════════════════════════════════════════════
if results:
    nb   = sum(1 for r in results if r["signal"]=="BULL")
    nr   = sum(1 for r in results if r["signal"]=="BEAR")
    nvs  = sum(1 for r in results if r["strength"]>=80)
    nsig = sum(1 for r in results if r["signal"]!="NONE")
    avgs = np.mean([r["strength"] for r in results if r["signal"]!="NONE"] or [0])
    nk   = sum(1 for r in results if r.get("src")=="kite")
    ls_s = (st.session_state.last_scan.strftime("%H:%M  %d %b")
            if st.session_state.last_scan else "—")

    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-card" style="--accent:#0891b2;"><div class="sc-label">Scanned</div>
        <div class="sc-val">{len(results)}</div>
        <div class="sc-sub">Kite:{nk} · yf:{len(results)-nk}</div></div>
      <div class="stat-card" style="--accent:#16a34a;"><div class="sc-label">Bull Signals</div>
        <div class="sc-val">{nb}</div>
        <div class="sc-sub">{nb/len(results)*100:.1f}% of universe</div></div>
      <div class="stat-card" style="--accent:#dc2626;"><div class="sc-label">Bear Signals</div>
        <div class="sc-val">{nr}</div>
        <div class="sc-sub">{nr/len(results)*100:.1f}% of universe</div></div>
      <div class="stat-card" style="--accent:#f59e0b;"><div class="sc-label">Very Strong ≥80%</div>
        <div class="sc-val">{nvs}</div>
        <div class="sc-sub">High confidence</div></div>
      <div class="stat-card" style="--accent:#7c3aed;"><div class="sc-label">Avg Strength</div>
        <div class="sc-val">{avgs:.1f}%</div>
        <div class="sc-sub">Across {nsig} signals</div></div>
      <div class="stat-card" style="--accent:#64748b;"><div class="sc-label">Last Scan</div>
        <div class="sc-val" style="font-size:16px;">{ls_s}</div>
        <div class="sc-sub">30-min auto in mkt hours</div></div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.alerts:
        a  = st.session_state.alerts[0]
        bl = a["signal"]=="BULL"
        cl = "#15803d" if bl else "#b91c1c"
        bg = "#f0fdf4" if bl else "#fef2f2"
        st.markdown(f"""
        <div class="alert-box" style="--ac:{cl};--abg:{bg};">
          <div>
            <span style="color:{cl};font-weight:700;font-size:12px;">
              {'↑ BULL' if bl else '↓ BEAR'} ALERT — {a['ticker']}</span>
            <span style="color:#64748b;font-size:10px;margin-left:10px;">
              {a['name']}  ·  {a['str']:.1f}%  ·  Rs.{a['price']:,.0f}  ·  {a['ts']} IST</span>
          </div>
          <span style="color:{cl};font-size:18px;font-weight:700;">{a['str']:.1f}%</span>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# FILTER + TABLE
# ══════════════════════════════════════════════════════════════════════════════
if results:
    rows = list(results)
    if search:
        s = search.upper()
        rows = [r for r in rows if s in r["ticker"] or s in r["name"].upper()]
    if sig_f=="↑ Bull":         rows=[r for r in rows if r["signal"]=="BULL"]
    elif sig_f=="↓ Bear":       rows=[r for r in rows if r["signal"]=="BEAR"]
    elif sig_f=="Strong >=80%": rows=[r for r in rows if r["strength"]>=80]
    elif sig_f=="Has Signal":   rows=[r for r in rows if r["signal"]!="NONE"]
    if rsi_f=="OB >70":         rows=[r for r in rows if r["rsi"]>=70]
    elif rsi_f=="OS <30":       rows=[r for r in rows if r["rsi"]<=30]
    elif rsi_f=="Neutral":      rows=[r for r in rows if 30<r["rsi"]<70]
    if sort_f=="Strength ↓":    rows.sort(key=lambda x:(x["signal"]!="NONE",x["strength"]),reverse=True)
    elif sort_f=="Change % ↓":  rows.sort(key=lambda x:abs(x["chg"]),reverse=True)
    elif sort_f=="RSI ↓":       rows.sort(key=lambda x:x["rsi"],reverse=True)
    elif sort_f=="Price ↓":     rows.sort(key=lambda x:x["price"],reverse=True)
    elif sort_f=="A→Z":         rows.sort(key=lambda x:x["ticker"])

    def _c(v):
        c="pos" if v>=0 else "neg"
        return f'<span class="{c}">{"+" if v>=0 else ""}{v:.2f}%</span>'
    def _d(v,s=4):
        c="pos" if v>0 else("neg" if v<0 else"neu")
        return f'<span class="{c}">{"+" if v>0 else""}{v:.{s}f}</span>'
    def _r(v):
        c="rsi-ob" if v>=70 else("rsi-os" if v<=30 else"rsi-n")
        return f'<span class="{c}">{v:.1f}</span>'
    def _s(v,bull):
        if v==0: return '<span class="neu">—</span>'
        sc=scol(v,bull)
        return (f'<div class="sc">'
                f'<span style="font-weight:600;font-size:11px;min-width:36px;'
                f'text-align:right;color:{sc};">{v:.1f}%</span>'
                f'<div class="st"><div class="sf" style="width:{v}%;background:{sc};"></div></div>'
                f'</div>')
    def _rt(v):
        if v==0: return '<span class="rvw">—</span>'
        rt,cls,_=get_rating(v)
        return f'<span class="{cls}">{rt}</span>'
    def _sg(s):
        if s=="BULL": return '<span class="badge bb">↑ BULL</span>'
        if s=="BEAR": return '<span class="badge be">↓ BEAR</span>'
        return '<span class="badge bn">—</span>'
    def _src(s):
        return ('<span class="badge bk">KITE</span>' if s=="kite"
                else '<span class="badge by">YF</span>')

    tbody=""
    for r in rows:
        bull=r["signal"]=="BULL"; bear=r["signal"]=="BEAR"
        rc="br" if bull else("rr" if bear else"")
        nm=r.get("name",""); tk=r["ticker"]
        pf=f'Rs.{r["price"]:,.0f}' if r["price"]>=100 else f'Rs.{r["price"]:,.2f}'
        tbody+=(f'<tr class="{rc}">'
                f'<td><span class="tk" title="{nm}">{tk}</span></td>'
                f'<td>{pf}</td>'
                f'<td>{_c(r["chg"])}</td>'
                f'<td class="hc">Rs.{r["hlc3"]:,.2f}</td>'
                f'<td class="hc">Rs.{r["ama"]:,.2f}</td>'
                f'<td class="hs">Rs.{r["ema70"]:,.2f}</td>'
                f'<td>{_d(r["d1"])}</td>'
                f'<td>{_d(r["d2"],4)}</td>'
                f'<td>{_d(r["d3"],2)}</td>'
                f'<td>{_r(r["rsi"])}</td>'
                f'<td>{_s(r["strength"],bull)}</td>'
                f'<td>{_rt(r["strength"])}</td>'
                f'<td class="tc">{_sg(r["signal"])}</td>'
                f'<td class="tc">{_src(r.get("src","yf"))}</td>'
                f'</tr>')

    st.markdown(f"""
    <div class="tbl-card">
      <div class="tbl-hdr">
        <span class="tbl-title">NIFTY 500 — GRADIENT SIGNAL SCANNER</span>
        <span class="tbl-cnt">{len(rows)} results</span>
      </div>
      <div class="tbl-scroll">
        <table class="t">
          <thead><tr>
            <th>TICKER</th><th>PRICE</th><th>CHG%</th>
            <th>HLC3</th><th>AMA</th><th>EMA70</th>
            <th>f'(x)%</th><th>f''(x)%</th><th>f'''(x)%</th>
            <th>RSI</th><th>STR%</th><th>RATING</th>
            <th class="tc">SIGNAL</th><th class="tc">SRC</th>
          </tr></thead>
          <tbody>{tbody}</tbody>
        </table>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    fa, fb, fc = st.columns([4,1,1])
    with fa:
        ls_l = (st.session_state.last_scan.strftime("%d %b %Y  %H:%M:%S IST")
                if st.session_state.last_scan else "—")
        st.markdown(
            f'<div style="font-size:10px;color:#94a3b8;padding-top:6px;">'
            f'{len(rows)} rows  ·  {len(results)} scanned  ·  Last: {ls_l}'
            f'  ·  Source: {"Kite API" if st.session_state.kite_connected else "yfinance"}'
            f'  ·  Not investment advice</div>',
            unsafe_allow_html=True)
    with fb:
        df_o = pd.DataFrame([{
            "Ticker":    r["ticker"], "Price":    round(r["price"],2),
            "Chg%":     round(r["chg"],2), "HLC3": r["hlc3"],
            "AMA":      r["ama"], "EMA70":   r["ema70"],
            "f'(x)%":  r["d1"], "f''(x)%": r["d2"], "f'''(x)%": r["d3"],
            "RSI":      r["rsi"], "Str%":   r["strength"],
            "Rating":   get_rating(r["strength"])[0] if r["signal"]!="NONE" else "—",
            "Signal":   r["signal"], "Source": r.get("src","yf"),
        } for r in rows])
        ts = datetime.now(IST).strftime("%Y%m%d_%H%M")
        st.download_button("⬇ Export CSV", df_o.to_csv(index=False),
            file_name=f"AMA_NIFTY500_{ts}.csv", mime="text/csv",
            use_container_width=True)
    with fc:
        if st.session_state.alerts:
            with st.expander(f"🔔 Alerts ({len(st.session_state.alerts)})"):
                for a in st.session_state.alerts[:20]:
                    bl=a["signal"]=="BULL"; cl="#15803d" if bl else "#b91c1c"
                    st.markdown(
                        f'<div style="font-size:10px;padding:4px 0;'
                        f'border-bottom:1px solid #f1f5f9;">'
                        f'<span style="color:{cl};font-weight:600;">'
                        f'{"↑" if bl else "↓"} {a["ticker"]}</span>'
                        f'  <span style="color:#94a3b8;">'
                        f'{a["str"]:.1f}%  ·  {a["ts"]}</span></div>',
                        unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:#fff;
         border:1px solid #e8eaf0;border-radius:12px;margin-top:10px;">
      <div style="font-size:36px;margin-bottom:10px;">⚡</div>
      <div style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:5px;">
        Ready to scan NIFTY 500</div>
      <div style="font-size:11px;color:#94a3b8;">
        Connect Kite API above for real-time data,
        or click Scan to use yfinance (EOD data).</div>
    </div>""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;color:#cbd5e1;font-size:9px;letter-spacing:1px;
     border-top:1px solid #e8eaf0;padding:8px 0;margin-top:10px;">
  AMA v3.0  ·  GRADIENT BACKPROP  ·  NIFTY 500  ·  Kite API + yfinance  ·
  Not investment advice
</div>""", unsafe_allow_html=True)

# Auto-rerun (market hours only, every 30 min)
if st.session_state.last_scan:
    now_c = datetime.now(IST)
    mc    = (now_c.weekday()<5
             and 9*60+15 <= now_c.hour*60+now_c.minute <= 15*60+30)
    if mc and int((now_c-st.session_state.last_scan).total_seconds()) >= REFRESH_SECS:
        time.sleep(2)
        st.rerun()
