"""
AMA v3.0 — Gradient Backprop + Reversal Strength
NIFTY 500 Universe | Zerodha Kite API (primary) + yfinance (fallback)
Real-time OHLC | 30-min refresh during market hours | Gmail + ntfy + Telegram alerts
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

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(
    page_title="AMA Gradient — NIFTY 500",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

REFRESH_SECS = 1800  # 30 min

# ── CSS ───────────────────────────────────────────────────────────────────────
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
.live-dot{width:6px;height:6px;border-radius:50%;background:#16a34a;animation:pulse 1.4s infinite;}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
.nav-time{font-size:11px;color:#64748b;font-family:'JetBrains Mono',monospace;}
.mkt-open{background:#f0fdf4;border:1px solid #bbf7d0;color:#16a34a;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;}
.mkt-close{background:#fef2f2;border:1px solid #fecaca;color:#dc2626;border-radius:20px;padding:3px 10px;font-size:10px;font-weight:600;}

/* Kite API status banner */
.kite-ok{background:#f0fdf4;border:1px solid #bbf7d0;border-left:4px solid #16a34a;border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px;color:#15803d;}
.kite-warn{background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #f59e0b;border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px;color:#92400e;}
.kite-err{background:#fef2f2;border:1px solid #fecaca;border-left:4px solid #dc2626;border-radius:8px;padding:8px 14px;margin-bottom:8px;font-size:11px;color:#b91c1c;}

.stats-row{display:flex;gap:10px;margin-bottom:10px;}
.stat-card{flex:1;background:#fff;border:1px solid #e8eaf0;border-radius:10px;padding:12px 16px;box-shadow:0 1px 4px rgba(0,0,0,.04);}
.sc-label{font-size:10px;font-weight:500;color:#94a3b8;letter-spacing:.8px;text-transform:uppercase;}
.sc-val{font-size:22px;font-weight:700;margin-top:2px;color:var(--accent);}
.sc-sub{font-size:10px;color:#cbd5e1;margin-top:1px;}

.alert-box{border-radius:10px;padding:10px 16px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;border-left:4px solid var(--alert-col);background:var(--alert-bg);box-shadow:0 1px 4px rgba(0,0,0,.04);}

.tbl-card{background:#fff;border:1px solid #e8eaf0;border-radius:10px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.05);}
.tbl-header{background:#f8f9fc;border-bottom:1px solid #e8eaf0;padding:8px 14px;display:flex;justify-content:space-between;align-items:center;}
.tbl-title{font-size:11px;font-weight:600;color:#475569;letter-spacing:.5px;}
.tbl-count{font-size:10px;color:#94a3b8;}
.tbl-scroll{max-height:68vh;overflow-y:auto;}
.tbl-scroll::-webkit-scrollbar{width:4px;}
.tbl-scroll::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:4px;}

table.ama{width:100%;border-collapse:collapse;font-size:11px;}
table.ama thead th{background:#f8f9fc;color:#64748b;font-size:9px;font-weight:600;letter-spacing:1px;text-transform:uppercase;padding:8px 12px;text-align:right;border-bottom:1px solid #e8eaf0;position:sticky;top:0;z-index:5;white-space:nowrap;}
table.ama thead th:nth-child(1){text-align:left;min-width:90px;}
table.ama thead th.th-src{text-align:center;}
table.ama thead th.th-sig{text-align:center;}
table.ama tbody tr{border-bottom:1px solid #f1f5f9;transition:background .1s;}
table.ama tbody tr:hover{background:#f8faff;}
table.ama tbody tr.bull-row{background:#fafffe;}
table.ama tbody tr.bear-row{background:#fffafa;}
table.ama tbody tr.bull-row:hover{background:#f0fdf8;}
table.ama tbody tr.bear-row:hover{background:#fff5f5;}
table.ama tbody td{padding:7px 12px;text-align:right;color:#334155;font-family:'JetBrains Mono',monospace;font-size:11px;white-space:nowrap;}
table.ama tbody td:nth-child(1){text-align:left;font-family:'Inter',sans-serif;}
table.ama tbody td.td-sig{text-align:center;}
table.ama tbody td.td-src{text-align:center;}

.tk{font-weight:700;color:#1a1d2e;font-size:11px;cursor:default;}
.pos{color:#16a34a;font-weight:600;}
.neg{color:#dc2626;font-weight:600;}
.neu{color:#64748b;}
.hl-cyan{color:#0891b2;font-weight:600;}
.hl-slate{color:#475569;}

.badge{display:inline-flex;align-items:center;gap:3px;padding:2px 8px;border-radius:20px;font-size:9px;font-weight:700;letter-spacing:.5px;font-family:'Inter',sans-serif;}
.b-bull{background:#dcfce7;color:#15803d;border:1px solid #bbf7d0;}
.b-bear{background:#fee2e2;color:#b91c1c;border:1px solid #fecaca;}
.b-none{background:#f1f5f9;color:#94a3b8;border:1px solid #e2e8f0;}
.b-kite{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;font-size:8px;}
.b-yf{background:#f5f3ff;color:#6d28d9;border:1px solid #ddd6fe;font-size:8px;}

.str-cell{display:flex;align-items:center;gap:6px;justify-content:flex-end;}
.str-num{font-weight:600;font-size:11px;min-width:36px;text-align:right;}
.str-track{height:4px;width:44px;background:#e2e8f0;border-radius:3px;flex-shrink:0;}
.str-fill{height:4px;border-radius:3px;}

.rt-vs{color:#15803d;font-weight:600;font-size:10px;}
.rt-s{color:#16a34a;font-weight:500;font-size:10px;}
.rt-m{color:#d97706;font-weight:500;font-size:10px;}
.rt-w{color:#ea580c;font-weight:500;font-size:10px;}
.rt-vw{color:#94a3b8;font-weight:400;font-size:10px;}

.rsi-ob{color:#dc2626;font-weight:600;}
.rsi-os{color:#16a34a;font-weight:600;}
.rsi-n{color:#475569;}

.stButton>button{background:#1a1d2e!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:'Inter',sans-serif!important;font-size:12px!important;font-weight:600!important;padding:8px 20px!important;}
.stButton>button:hover{opacity:.85!important;}
.stDownloadButton>button{background:#f1f5f9!important;color:#334155!important;border:1px solid #e2e8f0!important;border-radius:8px!important;font-size:11px!important;font-weight:500!important;}
.stProgress>div>div>div>div{background:#2d3561!important;border-radius:4px!important;}
label[data-testid="stWidgetLabel"]{font-size:11px!important;color:#64748b!important;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# KITE API LAYER
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def get_kite_client(api_key: str, access_token: str):
    """Initialise and cache KiteConnect client."""
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key.strip())
        kite.set_access_token(access_token.strip())
        # Validate by fetching profile
        profile = kite.profile()
        return kite, profile.get("user_name", "User"), None
    except ImportError:
        return None, None, "kiteconnect not installed — run: pip install kiteconnect"
    except Exception as e:
        return None, None, str(e)


def kite_login_url(api_key: str) -> str:
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key.strip())
        return kite.login_url()
    except Exception:
        return f"https://kite.zerodha.com/connect/login?api_key={api_key.strip()}&v=3"


def generate_access_token(api_key: str, api_secret: str, request_token: str) -> tuple[str, str]:
    """Exchange request_token for access_token."""
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key.strip())
        data = kite.generate_session(request_token.strip(), api_secret=api_secret.strip())
        return data["access_token"], ""
    except Exception as e:
        return "", str(e)


# Kite instrument lookup cache
@st.cache_data(ttl=86400, show_spinner=False)
def get_kite_instruments(api_key: str, access_token: str) -> dict:
    """Returns {NSE_SYMBOL: instrument_token} for NSE equities."""
    try:
        from kiteconnect import KiteConnect
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        instruments = kite.instruments("NSE")
        return {
            i["tradingsymbol"]: i["instrument_token"]
            for i in instruments
            if i["segment"] == "NSE"
        }
    except Exception:
        return {}


def fetch_kite_ohlc(
    kite,
    instrument_token: int,
    ticker: str,
    interval: str = "day",
    days_back: int = 90,
) -> pd.DataFrame | None:
    """Fetch historical OHLC from Kite. interval: minute/5minute/15minute/60minute/day."""
    try:
        from_dt = date.today() - timedelta(days=days_back)
        to_dt   = date.today()
        data = kite.historical_data(
            instrument_token,
            from_date=from_dt,
            to_date=to_dt,
            interval=interval,
        )
        if not data:
            return None
        df = pd.DataFrame(data)
        df.columns = [c.capitalize() for c in df.columns]
        df = df.rename(columns={"Date": "Date", "Open": "Open",
                                 "High": "High", "Low": "Low",
                                 "Close": "Close", "Volume": "Volume"})
        df = df.dropna(subset=["Close"])
        return df if len(df) > 20 else None
    except Exception:
        return None


def fetch_kite_quote(kite, instrument_token: int) -> dict | None:
    """Fetch live quote for a single instrument."""
    try:
        q = kite.quote([f"NSE:{instrument_token}"])
        return list(q.values())[0] if q else None
    except Exception:
        return None


# ── yfinance fallback ─────────────────────────────────────────────────────────
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_yf(ticker: str, period: str, interval: str) -> pd.DataFrame | None:
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
    fsc, ssc = 2.0 / (fast + 1), 2.0 / (slow + 1)
    n = len(hlc3)
    ama = np.empty(n); ama[0] = hlc3[0]
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
    ama = calc_kama(hlc3, p["er_len"], p["fast"], p["slow"])
    ema = float(pd.Series(close).ewm(span=p["ema_len"], adjust=False).mean().iloc[-1])
    rsi = calc_rsi(close, 14)
    n   = len(ama)
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
        mA  = np.max(np.abs(d2[lb:])); mD = np.max(np.abs(d1[lb:]) * np.abs(d2[lb:]))
        mJ  = np.max(np.abs(d3[lb:]) * 0.1)
        mx  = max(1e-9, mA * p["wa"] + mD * p["wb"] + mJ * p["wc"])
        strength = min(100.0, raw / mx * 100)
        if abs(d1v) > p["bd1"] and abs(d2v) > p["bd2"]:
            strength = min(100.0, strength * 1.25); boost = True
    sig = "NONE"
    if p["filt"]:
        if gfb and strength >= p["min_str"]:   sig = "BULL"
        elif gfr and strength >= p["min_str"]: sig = "BEAR"
    else:
        if gfb:  sig = "BULL"
        elif gfr: sig = "BEAR"
    return {
        "hlc3": round(float(hlc3[-1]), 2), "ama": round(float(ama[-1]), 2),
        "ema70": round(ema, 2), "d1": round(d1v, 4), "d2": round(d2v, 6),
        "d3": round(d3v, 4), "rsi": rsi, "strength": round(strength, 1),
        "signal": sig, "gf_bull": gfb, "gf_bear": gfr, "boost": boost,
        "er": round(er_v, 4),
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


# ══════════════════════════════════════════════════════════════════════════════
# PROCESS TICKER  (Kite first, yfinance fallback)
# ══════════════════════════════════════════════════════════════════════════════
def process_ticker(ticker: str, p: dict, kite=None, instruments: dict = None) -> dict | None:
    df   = None
    src  = "yf"

    # ── Try Kite ──────────────────────────────────────────────────────────────
    if kite and instruments:
        token = instruments.get(ticker)
        if token:
            kite_interval = p.get("kite_interval", "day")
            days = {"minute": 5, "5minute": 30, "15minute": 60,
                    "60minute": 90, "day": 90}.get(kite_interval, 90)
            df = fetch_kite_ohlc(kite, token, ticker, kite_interval, days)
            if df is not None:
                src = "kite"

    # ── Fallback to yfinance ──────────────────────────────────────────────────
    if df is None:
        df = fetch_yf(ticker, p["period"], p["interval"])

    if df is None:
        return None

    try:
        h = df["High"].values.astype(float)
        l = df["Low"].values.astype(float)
        c = df["Close"].values.astype(float)
        hlc3  = (h + l + c) / 3
        if len(hlc3) < p["er_len"] + 5:
            return None
        sig   = compute_signal(hlc3, c, p)
        price = float(c[-1])
        prev  = float(c[-2]) if len(c) > 1 else price

        # Live price from Kite quote (intraday accuracy)
        if src == "kite" and kite and instruments:
            token = instruments.get(ticker)
            if token:
                try:
                    q = kite.ltp([f"NSE:{ticker}"])
                    if q:
                        live = list(q.values())[0].get("last_price")
                        if live:
                            price = float(live)
                except Exception:
                    pass

        return {
            "ticker": ticker,
            "name":   NIFTY500.get(ticker, ticker),
            "price":  price, "prev": prev,
            "chg":    (price - prev) / prev * 100 if prev else 0.0,
            "src":    src,
            **sig,
        }
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# ALERT FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════
def _build_push_body(alerts: list, scan_time: str) -> tuple[str, str]:
    bull = [a for a in alerts if a["signal"] == "BULL"]
    bear = [a for a in alerts if a["signal"] == "BEAR"]
    title = f"AMA NIFTY500 | {len(bull)} BULL {len(bear)} BEAR | {scan_time} IST"
    lines = [f"VERY STRONG signals at {scan_time} IST"]
    if bull:
        lines.append("BULL: " + ", ".join(f"{a['ticker']}({a['str']:.0f}%)" for a in bull[:6]))
    if bear:
        lines.append("BEAR: " + ", ".join(f"{a['ticker']}({a['str']:.0f}%)" for a in bear[:6]))
    if len(alerts) > 12:
        lines.append(f"...and {len(alerts)-12} more")
    return title, "\n".join(lines)


def send_ntfy_push(topic: str, alerts: list, scan_time: str) -> tuple[bool, str]:
    if not topic or not alerts:
        return False, "No topic or no alerts"
    topic_clean = topic.strip().replace(" ", "-")
    title, body = _build_push_body(alerts, scan_time)
    try:
        import requests as _req
        resp = _req.post(
            f"https://ntfy.sh/{topic_clean}",
            data=body.encode("utf-8"),
            headers={"Title": title, "Priority": "high",
                     "Tags": "bell", "Content-Type": "text/plain"},
            timeout=12,
        )
        return (True, f"Push sent to '{topic_clean}'") if resp.status_code == 200 \
               else (False, f"ntfy HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        return False, f"ntfy error: {str(e)[:100]}"


def send_telegram_push(bot_token: str, chat_id: str,
                       alerts: list, scan_time: str) -> tuple[bool, str]:
    if not bot_token or not chat_id or not alerts:
        return False, "Missing credentials or no alerts"
    title, body = _build_push_body(alerts, scan_time)
    text = f"*{title}*\n\n{body}"
    try:
        import requests as _req
        resp = _req.post(
            f"https://api.telegram.org/bot{bot_token.strip()}/sendMessage",
            json={"chat_id": chat_id.strip(), "text": text, "parse_mode": "Markdown"},
            timeout=12,
        )
        if resp.status_code == 200:
            return True, f"Telegram sent to chat {chat_id}"
        return False, f"Telegram error: {resp.json().get('description', resp.text[:80])}"
    except Exception as e:
        return False, f"Telegram error: {str(e)[:100]}"


def build_email_html(alerts: list, scan_time: str, threshold: int) -> str:
    bull_rows = [a for a in alerts if a["signal"] == "BULL"]
    bear_rows = [a for a in alerts if a["signal"] == "BEAR"]
    def rows_html(items, color, arrow):
        if not items:
            return f'<tr><td colspan="5" style="padding:12px;color:#94a3b8;text-align:center;">No {arrow} signals</td></tr>'
        out = ""
        for a in items:
            out += (f'<tr style="border-bottom:1px solid #f1f5f9;">'
                    f'<td style="padding:8px 12px;font-weight:700;color:#1a1d2e;">{a["ticker"]}</td>'
                    f'<td style="padding:8px 12px;color:#64748b;font-size:11px;">{a["name"]}</td>'
                    f'<td style="padding:8px 12px;text-align:right;">Rs.{a["price"]:,.0f}</td>'
                    f'<td style="padding:8px 12px;text-align:right;font-weight:700;color:{color};">{a["str"]:.1f}%</td>'
                    f'<td style="padding:8px 12px;text-align:center;"><span style="background:{"#dcfce7" if arrow == "UP" else "#fee2e2"};color:{color};border-radius:12px;padding:2px 10px;font-size:10px;font-weight:700;">{arrow} {a["signal"]}</span></td>'
                    f'</tr>')
        return out
    return f"""<html><body style="font-family:Inter,sans-serif;background:#f8f9fc;margin:0;padding:20px;">
    <div style="max-width:700px;margin:0 auto;">
    <div style="background:#1a1d2e;border-radius:12px 12px 0 0;padding:20px 24px;">
    <div style="color:#f59e0b;font-size:18px;font-weight:700;">AMA Gradient Signal Alert</div>
    <div style="color:#94a3b8;font-size:11px;margin-top:4px;">NIFTY 500 | Scan: {scan_time} IST | Threshold: >={threshold}%</div>
    </div>
    <div style="background:#fff;padding:14px 24px;border-bottom:1px solid #e8eaf0;display:flex;gap:12px;">
    <div style="background:#dcfce7;border-radius:8px;padding:8px 16px;text-align:center;">
    <div style="font-size:20px;font-weight:700;color:#15803d;">{len(bull_rows)}</div>
    <div style="font-size:10px;color:#16a34a;font-weight:600;">BULL SIGNALS</div></div>
    <div style="background:#fee2e2;border-radius:8px;padding:8px 16px;text-align:center;">
    <div style="font-size:20px;font-weight:700;color:#b91c1c;">{len(bear_rows)}</div>
    <div style="font-size:10px;color:#dc2626;font-weight:600;">BEAR SIGNALS</div></div>
    </div>
    <div style="background:#fff;padding:0;">
    <div style="padding:10px 24px;background:#f0fdf4;border-bottom:1px solid #bbf7d0;">
    <span style="font-size:11px;font-weight:700;color:#15803d;">BULLISH REVERSALS</span></div>
    <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <thead><tr style="background:#f8f9fc;">
    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;">TICKER</th>
    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;">COMPANY</th>
    <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;">PRICE</th>
    <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;">STR%</th>
    <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:9px;">SIGNAL</th>
    </tr></thead><tbody>{rows_html(bull_rows, "#15803d", "UP")}</tbody></table></div>
    <div style="background:#fff;padding:0;">
    <div style="padding:10px 24px;background:#fef2f2;border-bottom:1px solid #fecaca;">
    <span style="font-size:11px;font-weight:700;color:#b91c1c;">BEARISH REVERSALS</span></div>
    <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <thead><tr style="background:#f8f9fc;">
    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;">TICKER</th>
    <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;">COMPANY</th>
    <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;">PRICE</th>
    <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;">STR%</th>
    <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:9px;">SIGNAL</th>
    </tr></thead><tbody>{rows_html(bear_rows, "#b91c1c", "DOWN")}</tbody></table></div>
    <div style="background:#f8f9fc;border-radius:0 0 12px 12px;padding:12px 24px;border-top:1px solid #e8eaf0;text-align:center;">
    <p style="font-size:10px;color:#94a3b8;margin:0;">AMA Gradient Backprop Engine | NIFTY 500 | Not investment advice.</p>
    </div></div></body></html>"""


def send_gmail_alert(sender: str, password: str, recipient: str,
                     alerts: list, scan_time: str, threshold: int) -> tuple[bool, str]:
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"AMA Signal Alert — {len(alerts)} signals >={threshold}% [{scan_time}]"
        msg["From"] = sender; msg["To"] = recipient
        msg.attach(MIMEText(build_email_html(alerts, scan_time, threshold), "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
            s.login(sender, password)
            s.sendmail(sender, recipient, msg.as_string())
        return True, f"Email sent to {recipient}"
    except smtplib.SMTPAuthenticationError:
        return False, "Auth failed — check Gmail App Password"
    except Exception as e:
        return False, f"Email error: {str(e)[:80]}"


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE + SECRETS
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("results",[]),("alerts",[]),("last_scan",None),("scanned",False),
             ("email_log",[]),("kite",None),("kite_user",""),("kite_err",""),
             ("instruments",{})]:
    if k not in st.session_state: st.session_state[k] = v

_SEC = st.secrets if hasattr(st, "secrets") else {}
def _secret(key, default=""): 
    try: return str(_SEC.get(key, default) or default)
    except: return default

for _k, _v in {
    "kite_api_key":     _secret("kite_api_key"),
    "kite_api_secret":  _secret("kite_api_secret"),
    "kite_access_token":_secret("kite_access_token"),
    "ntfy_topic":       _secret("ntfy_topic"),
    "ntfy_enabled":     _secret("ntfy_enabled","false").lower()=="true",
    "tg_token":         _secret("tg_token"),
    "tg_chat_id":       _secret("tg_chat_id"),
    "tg_enabled":       _secret("tg_enabled","false").lower()=="true",
    "gmail_sender":     _secret("gmail_sender"),
    "gmail_password":   _secret("gmail_password"),
    "gmail_recipient":  _secret("gmail_recipient"),
    "email_enabled":    _secret("email_enabled","false").lower()=="true",
}.items():
    if _k not in st.session_state: st.session_state[_k] = _v

def get_cred(key):
    sec = _secret(key)
    return sec if sec else str(st.session_state.get(key,"") or "")

params = dict(er_len=10, fast=6, slow=7, ema_len=70, lookback=20, min_str=50,
              filt=True, wa=0.35, wb=0.012, wc=0.50, bd1=1.0, bd2=0.5,
              period="3mo", interval="1d", kite_interval="day")

# ══════════════════════════════════════════════════════════════════════════════
# NAV BAR
# ══════════════════════════════════════════════════════════════════════════════
now   = datetime.now(IST)
_mins = now.hour * 60 + now.minute
mkt   = now.weekday() < 5 and 9*60+15 <= _mins <= 15*60+30
mkt_html = ('<span class="mkt-open">● NSE OPEN</span>' if mkt
            else '<span class="mkt-close">● NSE CLOSED</span>')
ls  = st.session_state.last_scan
nxt = ""
if ls:
    rem = max(0, REFRESH_SECS - int((now - ls).total_seconds()))
    nxt = f"Next scan in {rem//60:02d}:{rem%60:02d}"

kite_src = "Kite API" if st.session_state.kite else "yfinance (fallback)"
st.markdown(f"""
<div class="nav-bar">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:32px;height:32px;border-radius:8px;background:linear-gradient(135deg,#1a1d2e,#2d3561);
         display:flex;align-items:center;justify-content:center;font-size:14px;color:#f59e0b;font-weight:700;">⚡</div>
    <div>
      <div class="nav-title">AMA v3.0 — Gradient Backprop + Reversal Strength</div>
      <div class="nav-sub">NIFTY 500  ·  KAMA  ·  f'(x) f''(x) f'''(x)  ·  {kite_src}  ·  {nxt}</div>
    </div>
  </div>
  <div class="nav-right">
    <div class="nav-badge"><span class="live-dot"></span>LIVE</div>
    <span class="nav-time">{now.strftime('%H:%M:%S  %d %b %Y IST')}</span>
    {mkt_html}
  </div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# KITE API SETTINGS PANEL
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🔑  Zerodha Kite API Setup  —  click to configure", expanded=not st.session_state.kite):

    st.markdown("""
    <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
         padding:10px 14px;margin-bottom:10px;font-size:11px;color:#1e40af;">
    <b>Kite API gives you real-time OHLC, live prices, and intraday bars (1min/5min/15min).</b><br>
    Without it the app falls back to yfinance (EOD data only).<br><br>
    <b>One-time setup:</b><br>
    1. Go to <a href="https://developers.kite.trade" target="_blank" style="color:#1d4ed8;">developers.kite.trade</a>
       → Create App → copy <b>API Key</b> and <b>API Secret</b><br>
    2. Set redirect URL to: <code>https://127.0.0.1</code> (or your Streamlit Cloud URL)<br>
    3. Every trading day, generate a fresh <b>Access Token</b> using the flow below.<br>
    4. Save API Key + Secret in Streamlit Secrets for persistence.
    </div>
    """, unsafe_allow_html=True)

    k1, k2, k3 = st.columns([2, 2, 2])
    with k1:
        kite_api_key = st.text_input("Kite API Key",
            value=get_cred("kite_api_key"),
            placeholder="your_api_key",
            key="kite_api_key")
    with k2:
        kite_api_secret = st.text_input("Kite API Secret",
            value=get_cred("kite_api_secret"),
            type="password",
            placeholder="your_api_secret",
            key="kite_api_secret")
    with k3:
        kite_access_token = st.text_input("Access Token (daily)",
            value=get_cred("kite_access_token"),
            type="password",
            placeholder="paste today's access token",
            key="kite_access_token")

    ka1, ka2, ka3, ka4 = st.columns([2, 2, 1, 1])
    with ka1:
        if kite_api_key:
            login_url = kite_login_url(kite_api_key)
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:6px;
                 padding:8px 12px;font-size:11px;color:#15803d;">
            <b>Step 1:</b> <a href="{login_url}" target="_blank" style="color:#1d4ed8;">
            Click here to login to Kite</a> → approve → copy the <code>request_token</code>
            from the redirected URL
            </div>""", unsafe_allow_html=True)
    with ka2:
        req_token_input = st.text_input("Paste request_token from URL",
            placeholder="request_token from redirect URL",
            key="req_token_input")
    with ka3:
        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        if st.button("Generate Access Token", use_container_width=True):
            if kite_api_key and kite_api_secret and req_token_input:
                with st.spinner("Generating..."):
                    token, err = generate_access_token(
                        kite_api_key, kite_api_secret, req_token_input)
                if token:
                    st.session_state.kite_access_token = token
                    st.success(f"Access token generated! Save it to Secrets for persistence.")
                    st.code(token)
                else:
                    st.error(f"Failed: {err}")
            else:
                st.warning("Fill API Key, Secret and request_token first.")
    with ka4:
        st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
        if st.button("Connect Kite", use_container_width=True):
            if kite_api_key and kite_access_token:
                with st.spinner("Connecting..."):
                    kite_obj, user_name, err = get_kite_client(kite_api_key, kite_access_token)
                if kite_obj:
                    st.session_state.kite      = kite_obj
                    st.session_state.kite_user = user_name
                    st.session_state.kite_err  = ""
                    with st.spinner("Loading NSE instrument list..."):
                        st.session_state.instruments = get_kite_instruments(
                            kite_api_key, kite_access_token)
                    st.success(f"Connected as {user_name}  |  {len(st.session_state.instruments)} instruments loaded")
                else:
                    st.session_state.kite     = None
                    st.session_state.kite_err = err
                    st.error(f"Connection failed: {err}")
            else:
                st.warning("Enter API Key and Access Token first.")

    # Status line
    if st.session_state.kite:
        st.markdown(f"""<div class="kite-ok">
        ✅ Kite connected — {st.session_state.kite_user}  ·
        {len(st.session_state.instruments)} NSE instruments loaded  ·
        Real-time data active</div>""", unsafe_allow_html=True)
    elif st.session_state.kite_err:
        st.markdown(f'<div class="kite-err">❌ {st.session_state.kite_err}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="kite-warn">⚠️ Kite not connected — using yfinance (EOD) as fallback</div>',
                    unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:10px;color:#94a3b8;margin-top:6px;">
    💡 <b>Persist credentials:</b> Add to Streamlit Secrets →
    <code>kite_api_key</code>, <code>kite_api_secret</code>, <code>kite_access_token</code>
    (regenerate access token each trading day — it expires at midnight)
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# ALERT SETTINGS PANEL
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🔔  Alert Settings  —  Gmail + Mobile Push", expanded=False):
    tab_push, tab_gmail = st.tabs(["📱  Mobile Push (ntfy / Telegram)", "📧  Gmail"])

    with tab_push:
        push_method = st.radio("Push method", ["ntfy.sh", "Telegram Bot"],
                               horizontal=True, key="push_method")
        if push_method == "ntfy.sh":
            st.markdown("""<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
                 padding:8px 12px;margin-bottom:8px;font-size:11px;color:#1e40af;">
            Install <b>ntfy</b> app (Android/iOS) → tap + → subscribe to your topic name →
            enter same name below. Use hyphens only (no underscores).
            </div>""", unsafe_allow_html=True)
            np1, np2 = st.columns([3, 1])
            with np1:
                ntfy_topic = st.text_input("ntfy topic (hyphens only)",
                    value=get_cred("ntfy_topic"), placeholder="ama-nifty-yourname-2024",
                    key="ntfy_topic")
            with np2:
                st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
                ntfy_enabled = st.toggle("Enable", value=st.session_state.get("ntfy_enabled",False), key="ntfy_enabled")
                if st.button("Test Push", use_container_width=True, key="btn_ntfy"):
                    if ntfy_topic:
                        ok, msg = send_ntfy_push(ntfy_topic, [
                            {"ticker":"RELIANCE","signal":"BULL","str":91.2,"price":2950.0},
                            {"ticker":"TCS","signal":"BEAR","str":84.7,"price":4120.0}], now.strftime("%H:%M"))
                        st.success(msg) if ok else st.error(msg)
                    else: st.warning("Enter topic name first.")
        else:
            st.markdown("""<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;
                 padding:8px 12px;margin-bottom:8px;font-size:11px;color:#0c4a6e;">
            Telegram: @BotFather → /newbot → copy token. Then send msg to bot →
            open api.telegram.org/bot&lt;TOKEN&gt;/getUpdates → copy chat id.
            </div>""", unsafe_allow_html=True)
            tg1, tg2, tg3 = st.columns([3, 2, 1])
            with tg1:
                tg_token = st.text_input("Bot Token", value=get_cred("tg_token"),
                    type="password", placeholder="123456:ABCdef...", key="tg_token")
            with tg2:
                tg_chat_id = st.text_input("Chat ID", value=get_cred("tg_chat_id"),
                    placeholder="123456789", key="tg_chat_id")
            with tg3:
                st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
                tg_enabled = st.toggle("Enable", value=st.session_state.get("tg_enabled",False), key="tg_enabled")
                if st.button("Test", use_container_width=True, key="btn_tg"):
                    if tg_token and tg_chat_id:
                        ok, msg = send_telegram_push(tg_token, tg_chat_id, [
                            {"ticker":"RELIANCE","signal":"BULL","str":91.2,"price":2950.0}], now.strftime("%H:%M"))
                        st.success(msg) if ok else st.error(msg)
                    else: st.warning("Enter token and chat ID first.")

    with tab_gmail:
        gc1, gc2, gc3 = st.columns([2, 2, 1])
        with gc1:
            gmail_sender   = st.text_input("Gmail (sender)", value=get_cred("gmail_sender"),
                placeholder="you@gmail.com", key="gmail_sender")
            gmail_password = st.text_input("App Password", value=get_cred("gmail_password"),
                type="password", placeholder="abcd efgh ijkl mnop", key="gmail_password")
        with gc2:
            gmail_recipient = st.text_input("Recipient", value=get_cred("gmail_recipient"),
                placeholder="recipient@gmail.com", key="gmail_recipient")
            alert_threshold = st.slider("Threshold %", 50, 100, 80, 5, key="alert_threshold")
        with gc3:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            email_enabled = st.toggle("Enable email", value=st.session_state.get("email_enabled",False), key="email_enabled")
            if st.button("Test Email", use_container_width=True, key="btn_email"):
                if gmail_sender and gmail_password and gmail_recipient:
                    ok, msg = send_gmail_alert(gmail_sender.strip(),
                        gmail_password.replace(" ",""), gmail_recipient.strip(),
                        [{"ticker":"RELIANCE","name":"Reliance Industries","signal":"BULL","str":87.5,"price":2950.0}],
                        now.strftime("%H:%M:%S"), alert_threshold)
                    st.success(msg) if ok else st.error(msg)
                else: st.warning("Fill all email fields first.")
        if st.session_state.email_log:
            st.caption("  ·  ".join(st.session_state.email_log[-5:]))


# ══════════════════════════════════════════════════════════════════════════════
# CONTROLS ROW
# ══════════════════════════════════════════════════════════════════════════════
c1,c2,c3,c4,c5,c6,c7,c8,c9 = st.columns([2.5,1.4,1.4,1.4,1.1,1.1,1.1,1,1])
with c1: search = st.text_input("","",placeholder="🔍 Search ticker…",label_visibility="collapsed")
with c2: universe = st.selectbox("",["NIFTY 500","NIFTY 50","NIFTY Next 50","Custom"],label_visibility="collapsed")
with c3: sig_f = st.selectbox("",["All","↑ Bull","↓ Bear","Strong >=80%","Has Signal"],label_visibility="collapsed")
with c4: sort_f = st.selectbox("",["Strength ↓","Change % ↓","RSI ↓","Price ↓","A→Z"],label_visibility="collapsed")
with c5: rsi_f = st.selectbox("",["RSI: All","OB >70","OS <30","Neutral"],label_visibility="collapsed")
with c6:
    period = st.selectbox("",["3mo","6mo","1y","2y"],label_visibility="collapsed")
    params["period"] = period
with c7:
    if st.session_state.kite:
        kite_interval = st.selectbox("",["day","60minute","15minute","5minute","minute"],
                                     label_visibility="collapsed", key="kite_interval_sel")
        params["kite_interval"] = kite_interval
    else:
        min_str_ui = st.selectbox("",["Min 50%","Min 60%","Min 70%","Min 80%","No Filter"],
                                   label_visibility="collapsed")
        msm = {"Min 50%":50,"Min 60%":60,"Min 70%":70,"Min 80%":80,"No Filter":0}
        params["min_str"] = msm[min_str_ui]; params["filt"] = params["min_str"] > 0
with c8:
    min_str_ui2 = st.selectbox("",["Min 50%","Min 60%","Min 70%","Min 80%","No Filter"],
                                label_visibility="collapsed", key="min_str_sel2")
    msm2 = {"Min 50%":50,"Min 60%":60,"Min 70%":70,"Min 80%":80,"No Filter":0}
    params["min_str"] = msm2[min_str_ui2]; params["filt"] = params["min_str"] > 0
with c9: run_btn = st.button("⚡  Scan", use_container_width=True)

tickers_all = list(NIFTY500.keys())
if universe == "NIFTY 50":        scan_list = tickers_all[:50]
elif universe == "NIFTY Next 50":  scan_list = tickers_all[50:100]
elif universe == "Custom":
    scan_list = st.multiselect("Tickers:", tickers_all,
        default=["RELIANCE","TCS","INFY","HDFCBANK","SBIN"])
    if not scan_list: scan_list = tickers_all[:50]
else: scan_list = tickers_all

# Auto-refresh (market hours only)
elapsed = int((now - ls).total_seconds()) if ls else REFRESH_SECS + 1
if mkt and elapsed >= REFRESH_SECS: run_btn = True
if not st.session_state.scanned: run_btn = True

# ══════════════════════════════════════════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════════════════════════════════════════
if run_btn:
    prog = st.progress(0, text="Starting scan…")
    results, failed = [], []
    kite_obj    = st.session_state.kite
    instruments = st.session_state.instruments
    for idx, tk in enumerate(scan_list):
        prog.progress((idx+1)/len(scan_list), text=f"Scanning {tk}  ({idx+1}/{len(scan_list)})")
        r = process_ticker(tk, params, kite_obj, instruments)
        if r: results.append(r)
        else: failed.append(tk)
    prog.empty()

    scan_time = datetime.now(IST).strftime("%H:%M:%S")
    thr = 80
    new_alerts = [{"ts":scan_time,"ticker":r["ticker"],"name":r["name"],
                   "signal":r["signal"],"str":r["strength"],"price":r["price"]}
                  for r in results if r["signal"]!="NONE" and r["strength"]>=thr]

    st.session_state.alerts    = (new_alerts + st.session_state.alerts)[:100]
    st.session_state.results   = results
    st.session_state.last_scan = datetime.now(IST)
    st.session_state.scanned   = True

    # Send notifications
    if get_cred("email_enabled")=="True" or st.session_state.get("email_enabled") and new_alerts:
        if get_cred("gmail_sender") and get_cred("gmail_password") and get_cred("gmail_recipient"):
            ok,msg = send_gmail_alert(get_cred("gmail_sender").strip(),
                get_cred("gmail_password").replace(" ",""),
                get_cred("gmail_recipient").strip(), new_alerts, scan_time, thr)
            st.session_state.email_log = ([f"{scan_time}: {'OK' if ok else 'FAIL'} email — {msg}"] + st.session_state.email_log)[:10]

    if (get_cred("ntfy_enabled")=="True" or st.session_state.get("ntfy_enabled")) and new_alerts:
        if get_cred("ntfy_topic").strip():
            ok,msg = send_ntfy_push(get_cred("ntfy_topic"), new_alerts, scan_time)
            st.session_state.email_log = ([f"{scan_time}: {'OK' if ok else 'FAIL'} ntfy — {msg}"] + st.session_state.email_log)[:10]

    if (get_cred("tg_enabled")=="True" or st.session_state.get("tg_enabled")) and new_alerts:
        if get_cred("tg_token").strip() and get_cred("tg_chat_id").strip():
            ok,msg = send_telegram_push(get_cred("tg_token"), get_cred("tg_chat_id"), new_alerts, scan_time)
            st.session_state.email_log = ([f"{scan_time}: {'OK' if ok else 'FAIL'} telegram — {msg}"] + st.session_state.email_log)[:10]

    kite_count = sum(1 for r in results if r.get("src")=="kite")
    yf_count   = len(results) - kite_count
    info_parts = [f"Scan complete — {len(results)} tickers"]
    if kite_obj: info_parts.append(f"Kite: {kite_count}  yfinance: {yf_count}")
    if failed:   info_parts.append(f"Failed: {len(failed)}")
    st.caption("  ·  ".join(info_parts))

results = st.session_state.results

# ══════════════════════════════════════════════════════════════════════════════
# STATS BAR
# ══════════════════════════════════════════════════════════════════════════════
if results:
    n_bull = sum(1 for r in results if r["signal"]=="BULL")
    n_bear = sum(1 for r in results if r["signal"]=="BEAR")
    n_vs   = sum(1 for r in results if r["strength"]>=80)
    n_sig  = sum(1 for r in results if r["signal"]!="NONE")
    avg_s  = np.mean([r["strength"] for r in results if r["signal"]!="NONE"] or [0])
    n_kite = sum(1 for r in results if r.get("src")=="kite")
    ls_s   = st.session_state.last_scan.strftime("%H:%M  %d %b") if st.session_state.last_scan else "—"

    st.markdown(f"""
    <div class="stats-row">
      <div class="stat-card" style="--accent:#0891b2;"><div class="sc-label">Scanned</div>
        <div class="sc-val">{len(results)}</div><div class="sc-sub">Kite: {n_kite} | yf: {len(results)-n_kite}</div></div>
      <div class="stat-card" style="--accent:#16a34a;"><div class="sc-label">Bull Signals</div>
        <div class="sc-val">{n_bull}</div><div class="sc-sub">{n_bull/len(results)*100:.1f}% of universe</div></div>
      <div class="stat-card" style="--accent:#dc2626;"><div class="sc-label">Bear Signals</div>
        <div class="sc-val">{n_bear}</div><div class="sc-sub">{n_bear/len(results)*100:.1f}% of universe</div></div>
      <div class="stat-card" style="--accent:#f59e0b;"><div class="sc-label">Very Strong >=80%</div>
        <div class="sc-val">{n_vs}</div><div class="sc-sub">High confidence signals</div></div>
      <div class="stat-card" style="--accent:#7c3aed;"><div class="sc-label">Avg Strength</div>
        <div class="sc-val">{avg_s:.1f}%</div><div class="sc-sub">Across {n_sig} active signals</div></div>
      <div class="stat-card" style="--accent:#64748b;"><div class="sc-label">Last Scan</div>
        <div class="sc-val" style="font-size:16px;">{ls_s}</div>
        <div class="sc-sub">30-min refresh in market hours</div></div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.alerts:
        a = st.session_state.alerts[0]
        bull = a["signal"]=="BULL"
        col  = "#15803d" if bull else "#b91c1c"
        bg   = "#f0fdf4" if bull else "#fef2f2"
        st.markdown(f"""
        <div class="alert-box" style="--alert-col:{col};--alert-bg:{bg};">
          <div><span style="color:{col};font-weight:700;font-size:12px;">
            {'UP' if bull else 'DN'} ALERT — {a['ticker']}</span>
            <span style="color:#64748b;font-size:10px;margin-left:12px;">
            {a['name']}  ·  {a['str']:.1f}%  ·  Rs.{a['price']:,.0f}  ·  {a['ts']}</span>
          </div>
          <span style="color:{col};font-size:18px;font-weight:700;">{a['str']:.1f}%</span>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTER + TABLE
# ══════════════════════════════════════════════════════════════════════════════
if results:
    rows = list(results)
    if search:
        s = search.upper()
        rows = [r for r in rows if s in r["ticker"] or s in r["name"].upper()]
    if sig_f=="↑ Bull":          rows=[r for r in rows if r["signal"]=="BULL"]
    elif sig_f=="↓ Bear":        rows=[r for r in rows if r["signal"]=="BEAR"]
    elif sig_f=="Strong >=80%":  rows=[r for r in rows if r["strength"]>=80]
    elif sig_f=="Has Signal":    rows=[r for r in rows if r["signal"]!="NONE"]
    if rsi_f=="OB >70":          rows=[r for r in rows if r["rsi"]>=70]
    elif rsi_f=="OS <30":        rows=[r for r in rows if r["rsi"]<=30]
    elif rsi_f=="Neutral":       rows=[r for r in rows if 30<r["rsi"]<70]
    if sort_f=="Strength ↓":     rows.sort(key=lambda x:(x["signal"]!="NONE",x["strength"]),reverse=True)
    elif sort_f=="Change % ↓":   rows.sort(key=lambda x:abs(x["chg"]),reverse=True)
    elif sort_f=="RSI ↓":        rows.sort(key=lambda x:x["rsi"],reverse=True)
    elif sort_f=="Price ↓":      rows.sort(key=lambda x:x["price"],reverse=True)
    elif sort_f=="A→Z":          rows.sort(key=lambda x:x["ticker"])

    def _chg(v):
        c="pos" if v>=0 else "neg"
        return f'<span class="{c}">{"+" if v>=0 else ""}{v:.2f}%</span>'
    def _der(v,s=4):
        c="pos" if v>0 else("neg" if v<0 else"neu")
        return f'<span class="{c}">{"+" if v>0 else""}{v:.{s}f}</span>'
    def _rsi(v):
        c="rsi-ob" if v>=70 else("rsi-os" if v<=30 else"rsi-n")
        return f'<span class="{c}">{v:.1f}</span>'
    def _str(v,bull):
        if v==0: return '<span class="neu">—</span>'
        sc=str_col(v,bull)
        return(f'<div class="str-cell"><span class="str-num" style="color:{sc};">{v:.1f}%</span>'
               f'<div class="str-track"><div class="str-fill" style="width:{v}%;background:{sc};"></div></div></div>')
    def _rt(v):
        if v==0: return '<span class="rt-vw">—</span>'
        rt,cls,_=get_rating(v)
        return f'<span class="{cls}">{rt}</span>'
    def _sig(s):
        if s=="BULL": return '<span class="badge b-bull">BULL</span>'
        if s=="BEAR": return '<span class="badge b-bear">BEAR</span>'
        return '<span class="badge b-none">—</span>'
    def _src(s):
        if s=="kite": return '<span class="badge b-kite">KITE</span>'
        return '<span class="badge b-yf">YF</span>'

    tbody=""
    for r in rows:
        bull=r["signal"]=="BULL"; bear=r["signal"]=="BEAR"
        rc="bull-row" if bull else("bear-row" if bear else"")
        nm=r.get("name",""); tk=r["ticker"]
        p_fmt=f'Rs.{r["price"]:,.0f}' if r["price"]>=100 else f'Rs.{r["price"]:,.2f}'
        tbody+=(f'<tr class="{rc}">'
                f'<td><span class="tk" title="{nm}">{tk}</span></td>'
                f'<td>{p_fmt}</td>'
                f'<td>{_chg(r["chg"])}</td>'
                f'<td class="hl-cyan">Rs.{r["hlc3"]:,.2f}</td>'
                f'<td class="hl-cyan">Rs.{r["ama"]:,.2f}</td>'
                f'<td class="hl-slate">Rs.{r["ema70"]:,.2f}</td>'
                f'<td>{_der(r["d1"])}</td>'
                f'<td>{_der(r["d2"],4)}</td>'
                f'<td>{_der(r["d3"],2)}</td>'
                f'<td>{_rsi(r["rsi"])}</td>'
                f'<td>{_str(r["strength"],bull)}</td>'
                f'<td>{_rt(r["strength"])}</td>'
                f'<td class="td-sig">{_sig(r["signal"])}</td>'
                f'<td class="td-src">{_src(r.get("src","yf"))}</td>'
                f'</tr>')

    st.markdown(f"""
    <div class="tbl-card">
      <div class="tbl-header">
        <span class="tbl-title">NIFTY 500 — GRADIENT SIGNAL SCANNER</span>
        <span class="tbl-count">{len(rows)} results</span>
      </div>
      <div class="tbl-scroll">
        <table class="ama">
          <thead><tr>
            <th>TICKER</th><th>PRICE</th><th>CHG%</th>
            <th>HLC3</th><th>AMA</th><th>EMA70</th>
            <th>f'(x)%</th><th>f''(x)%</th><th>f'''(x)%</th>
            <th>RSI</th><th>STR%</th><th>RATING</th>
            <th class="th-sig">SIGNAL</th><th class="th-src">SRC</th>
          </tr></thead>
          <tbody>{tbody}</tbody>
        </table>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    fa,fb,fc = st.columns([4,1,1])
    with fa:
        ls_long=(st.session_state.last_scan.strftime("%d %b %Y  %H:%M:%S IST")
                 if st.session_state.last_scan else "—")
        src_txt="Kite API" if st.session_state.kite else "yfinance"
        st.markdown(f'<div style="font-size:10px;color:#94a3b8;padding-top:6px;">'
                    f'{len(rows)} rows  ·  {len(results)} scanned  ·  Last: {ls_long}'
                    f'  ·  Source: {src_txt}  ·  Not investment advice</div>',
                    unsafe_allow_html=True)
    with fb:
        df_out=pd.DataFrame([{"Ticker":r["ticker"],"Price":round(r["price"],2),
            "Chg%":round(r["chg"],2),"HLC3":r["hlc3"],"AMA":r["ama"],"EMA70":r["ema70"],
            "f'(x)%":r["d1"],"f''(x)%":r["d2"],"f'''(x)%":r["d3"],
            "RSI":r["rsi"],"Str%":r["strength"],
            "Rating":get_rating(r["strength"])[0] if r["signal"]!="NONE" else "—",
            "Signal":r["signal"],"Source":r.get("src","yf")} for r in rows])
        ts=datetime.now(IST).strftime("%Y%m%d_%H%M")
        st.download_button("Export CSV", df_out.to_csv(index=False),
            file_name=f"AMA_NIFTY500_{ts}.csv", mime="text/csv", use_container_width=True)
    with fc:
        if st.session_state.alerts:
            with st.expander(f"Alerts ({len(st.session_state.alerts)})"):
                for a in st.session_state.alerts[:20]:
                    bull_a=a["signal"]=="BULL"
                    col_a="#15803d" if bull_a else "#b91c1c"
                    st.markdown(f'<div style="font-size:10px;padding:4px 0;border-bottom:1px solid #f1f5f9;">'
                                f'<span style="color:{col_a};font-weight:600;">{"UP" if bull_a else "DN"} {a["ticker"]}</span>'
                                f'  <span style="color:#94a3b8;">{a["str"]:.1f}%  ·  {a["ts"]}</span></div>',
                                unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;background:#fff;border:1px solid #e8eaf0;border-radius:12px;margin-top:10px;">
      <div style="font-size:36px;margin-bottom:10px;">⚡</div>
      <div style="font-size:15px;font-weight:600;color:#1a1d2e;margin-bottom:5px;">Ready to scan NIFTY 500</div>
      <div style="font-size:11px;color:#94a3b8;">Connect Kite API above for real-time data, or click Scan to use yfinance (EOD).</div>
    </div>""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center;color:#cbd5e1;font-size:9px;letter-spacing:1px;
     border-top:1px solid #e8eaf0;padding:8px 0;margin-top:10px;">
  AMA v3.0  ·  GRADIENT BACKPROP ENGINE  ·  NIFTY 500  ·  Kite API + yfinance  ·  Not investment advice
</div>""", unsafe_allow_html=True)

# Auto-rerun (market hours only)
if st.session_state.last_scan:
    now_c = datetime.now(IST)
    mc    = now_c.weekday() < 5 and 9*60+15 <= now_c.hour*60+now_c.minute <= 15*60+30
    if mc and int((now_c - st.session_state.last_scan).total_seconds()) >= REFRESH_SECS:
        time.sleep(2); st.rerun()
