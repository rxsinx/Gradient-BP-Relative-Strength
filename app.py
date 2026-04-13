"""
AMA  — Gradient Backprop + Reversal Strength
NIFTY 500 Full Universe Scanner | 1-Hour Auto-Refresh | White Theme
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
IST = ZoneInfo('Asia/Kolkata')  # UTC+5:30
from nifty500 import NIFTY500

st.set_page_config(
    page_title="AMA Gradient — NIFTY 500",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

REFRESH_SECS = 1800


# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #f8f9fc !important;
    font-family: 'Inter', sans-serif !important;
    color: #1a1d2e !important;
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 1rem 1.5rem !important; max-width: 100% !important; }

.nav-bar {
    background: #ffffff; border: 1px solid #e8eaf0; border-radius: 10px;
    padding: 10px 20px; display: flex; justify-content: space-between;
    align-items: center; margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.nav-title { font-size: 14px; font-weight: 700; color: #1a1d2e; letter-spacing: -0.3px; }
.nav-sub   { font-size: 10px; color: #94a3b8; margin-top: 1px; letter-spacing: 0.5px; }
.nav-right { display: flex; align-items: center; gap: 14px; }
.nav-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 20px;
    padding: 3px 10px; font-size: 10px; font-weight: 600; color: #16a34a;
}
.live-dot { width:6px; height:6px; border-radius:50%; background:#16a34a; animation:pulse 1.4s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(.8)} }
.nav-time  { font-size: 11px; color: #64748b; font-family: 'JetBrains Mono', monospace; }
.mkt-open  { background:#f0fdf4; border:1px solid #bbf7d0; color:#16a34a; border-radius:20px; padding:3px 10px; font-size:10px; font-weight:600; }
.mkt-close { background:#fef2f2; border:1px solid #fecaca; color:#dc2626; border-radius:20px; padding:3px 10px; font-size:10px; font-weight:600; }

/* Email settings panel */
.email-panel {
    background: #ffffff; border: 1px solid #e8eaf0; border-radius: 10px;
    padding: 14px 18px; margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.email-panel-title { font-size: 11px; font-weight: 600; color: #475569; margin-bottom: 8px; }

.stats-row { display: flex; gap: 10px; margin-bottom: 10px; }
.stat-card {
    flex: 1; background: #ffffff; border: 1px solid #e8eaf0;
    border-radius: 10px; padding: 12px 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.sc-label { font-size: 10px; font-weight: 500; color: #94a3b8; letter-spacing: 0.8px; text-transform: uppercase; }
.sc-val   { font-size: 22px; font-weight: 700; margin-top: 2px; color: var(--accent); }
.sc-sub   { font-size: 10px; color: #cbd5e1; margin-top: 1px; }

.alert-box {
    border-radius: 10px; padding: 10px 16px; margin-bottom: 10px;
    display: flex; justify-content: space-between; align-items: center;
    border-left: 4px solid var(--alert-col); background: var(--alert-bg);
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

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
.tbl-scroll { max-height: 72vh; overflow-y: auto; }
.tbl-scroll::-webkit-scrollbar { width: 4px; }
.tbl-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }

table.ama { width: 100%; border-collapse: collapse; font-size: 11px; }
table.ama thead th {
    background: #f8f9fc; color: #64748b; font-size: 9px; font-weight: 600;
    letter-spacing: 1px; text-transform: uppercase;
    padding: 8px 12px; text-align: right; border-bottom: 1px solid #e8eaf0;
    position: sticky; top: 0; z-index: 5; white-space: nowrap;
}
table.ama thead th:nth-child(1) { text-align:left; min-width:90px; }
table.ama thead th.th-sig { text-align:center; }
table.ama tbody tr { border-bottom: 1px solid #f1f5f9; transition: background 0.1s; }
table.ama tbody tr:hover      { background: #f8faff; }
table.ama tbody tr.bull-row   { background: #fafffe; }
table.ama tbody tr.bear-row   { background: #fffafa; }
table.ama tbody tr.bull-row:hover { background: #f0fdf8; }
table.ama tbody tr.bear-row:hover { background: #fff5f5; }
table.ama tbody td {
    padding: 7px 12px; text-align: right; color: #334155;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; white-space: nowrap;
}
table.ama tbody td:nth-child(1) { text-align:left; font-family:'Inter',sans-serif; }
table.ama tbody td.td-sig { text-align:center; }

.tk   { font-weight: 700; color: #1a1d2e; font-size: 11px; cursor: default; }
.pos  { color: #16a34a; font-weight: 600; }
.neg  { color: #dc2626; font-weight: 600; }
.neu  { color: #64748b; }
.hl-cyan  { color: #0891b2; font-weight: 600; }
.hl-slate { color: #475569; }

.badge {
    display: inline-flex; align-items: center; gap: 3px;
    padding: 2px 8px; border-radius: 20px; font-size: 9px;
    font-weight: 700; letter-spacing: 0.5px; font-family: 'Inter', sans-serif;
}
.b-bull { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.b-bear { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
.b-none { background: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0; }

.str-cell  { display:flex; align-items:center; gap:6px; justify-content:flex-end; }
.str-num   { font-weight:600; font-size:11px; min-width:36px; text-align:right; }
.str-track { height:4px; width:44px; background:#e2e8f0; border-radius:3px; flex-shrink:0; }
.str-fill  { height:4px; border-radius:3px; }

.rt-vs { color:#15803d; font-weight:600; font-size:10px; }
.rt-s  { color:#16a34a; font-weight:500; font-size:10px; }
.rt-m  { color:#d97706; font-weight:500; font-size:10px; }
.rt-w  { color:#ea580c; font-weight:500; font-size:10px; }
.rt-vw { color:#94a3b8; font-weight:400; font-size:10px; }

.rsi-ob { color:#dc2626; font-weight:600; }
.rsi-os { color:#16a34a; font-weight:600; }
.rsi-n  { color:#475569; }

.stButton > button {
    background: #1a1d2e !important; color: #ffffff !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 12px !important;
    font-weight: 600 !important; padding: 8px 20px !important;
}
.stButton > button:hover { opacity: 0.85 !important; }
.stDownloadButton > button {
    background: #f1f5f9 !important; color: #334155 !important;
    border: 1px solid #e2e8f0 !important; border-radius: 8px !important;
    font-size: 11px !important; font-weight: 500 !important;
}
.stProgress > div > div > div > div { background: #2d3561 !important; border-radius: 4px !important; }
label[data-testid="stWidgetLabel"] { font-size: 11px !important; color: #64748b !important; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MATH ENGINE
# ══════════════════════════════════════════════════════════════════════════════
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

    el   = p["er_len"]
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
        if gfb and strength >= p["min_str"]:   sig = "BULL"
        elif gfr and strength >= p["min_str"]: sig = "BEAR"
    else:
        if gfb:  sig = "BULL"
        elif gfr: sig = "BEAR"

    return {
        "hlc3": round(float(hlc3[-1]), 2), "ama":  round(float(ama[-1]), 2),
        "ema70": round(ema, 2),            "d1":   round(d1v, 4),
        "d2":   round(d2v, 6),            "d3":   round(d3v, 4),
        "rsi":  rsi, "strength": round(strength, 1),
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


# ══════════════════════════════════════════════════════════════════════════════
# GMAIL ALERT ENGINE
# ══════════════════════════════════════════════════════════════════════════════
def build_email_html(alerts: list, scan_time: str, threshold: int) -> str:
    bull_rows = [a for a in alerts if a["signal"] == "BULL"]
    bear_rows = [a for a in alerts if a["signal"] == "BEAR"]

    def rows_html(items, color, arrow):
        if not items:
            return f'<tr><td colspan="5" style="padding:12px;color:#94a3b8;text-align:center;font-size:12px;">No {arrow} signals</td></tr>'
        out = ""
        for a in items:
            rt = get_rating(a["str"])[0]
            out += (
                f'<tr style="border-bottom:1px solid #f1f5f9;">'
                f'<td style="padding:8px 12px;font-weight:700;color:#1a1d2e;">{a["ticker"]}</td>'
                f'<td style="padding:8px 12px;color:#64748b;font-size:11px;">{a["name"]}</td>'
                f'<td style="padding:8px 12px;text-align:right;">₹{a["price"]:,.0f}</td>'
                f'<td style="padding:8px 12px;text-align:right;font-weight:700;color:{color};">{a["str"]:.1f}%</td>'
                f'<td style="padding:8px 12px;text-align:center;">'
                f'<span style="background:{"#dcfce7" if arrow=="↑" else "#fee2e2"};'
                f'color:{color};border-radius:12px;padding:2px 10px;font-size:10px;font-weight:700;">'
                f'{arrow} {a["signal"]}</span></td>'
                f'</tr>'
            )
        return out

    return f"""
    <html><body style="font-family:Inter,sans-serif;background:#f8f9fc;margin:0;padding:20px;">
    <div style="max-width:700px;margin:0 auto;">

      <!-- Header -->
      <div style="background:#1a1d2e;border-radius:12px 12px 0 0;padding:20px 24px;">
        <div style="color:#f59e0b;font-size:18px;font-weight:700;">⚡ AMA Gradient Signal Alert</div>
        <div style="color:#94a3b8;font-size:11px;margin-top:4px;">
          NIFTY 500 Universe · Scan: {scan_time} · Threshold: ≥{threshold}%
        </div>
      </div>

      <!-- Summary pills -->
      <div style="background:#ffffff;padding:14px 24px;display:flex;gap:12px;border-bottom:1px solid #e8eaf0;">
        <div style="background:#dcfce7;border-radius:8px;padding:8px 16px;text-align:center;">
          <div style="font-size:20px;font-weight:700;color:#15803d;">{len(bull_rows)}</div>
          <div style="font-size:10px;color:#16a34a;font-weight:600;">↑ BULL SIGNALS</div>
        </div>
        <div style="background:#fee2e2;border-radius:8px;padding:8px 16px;text-align:center;">
          <div style="font-size:20px;font-weight:700;color:#b91c1c;">{len(bear_rows)}</div>
          <div style="font-size:10px;color:#dc2626;font-weight:600;">↓ BEAR SIGNALS</div>
        </div>
        <div style="background:#fefce8;border-radius:8px;padding:8px 16px;text-align:center;">
          <div style="font-size:20px;font-weight:700;color:#92400e;">{len(alerts)}</div>
          <div style="font-size:10px;color:#d97706;font-weight:600;">TOTAL SIGNALS</div>
        </div>
      </div>

      <!-- Bull table -->
      <div style="background:#ffffff;padding:0;">
        <div style="padding:10px 24px;background:#f0fdf4;border-bottom:1px solid #bbf7d0;">
          <span style="font-size:11px;font-weight:700;color:#15803d;">↑ BULLISH REVERSALS</span>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead>
            <tr style="background:#f8f9fc;">
              <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;letter-spacing:1px;">TICKER</th>
              <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;letter-spacing:1px;">COMPANY</th>
              <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;letter-spacing:1px;">PRICE</th>
              <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;letter-spacing:1px;">STR %</th>
              <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:9px;letter-spacing:1px;">SIGNAL</th>
            </tr>
          </thead>
          <tbody>{rows_html(bull_rows, "#15803d", "↑")}</tbody>
        </table>
      </div>

      <!-- Bear table -->
      <div style="background:#ffffff;margin-top:1px;padding:0;">
        <div style="padding:10px 24px;background:#fef2f2;border-bottom:1px solid #fecaca;">
          <span style="font-size:11px;font-weight:700;color:#b91c1c;">↓ BEARISH REVERSALS</span>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead>
            <tr style="background:#f8f9fc;">
              <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;letter-spacing:1px;">TICKER</th>
              <th style="padding:8px 12px;text-align:left;color:#64748b;font-size:9px;letter-spacing:1px;">COMPANY</th>
              <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;letter-spacing:1px;">PRICE</th>
              <th style="padding:8px 12px;text-align:right;color:#64748b;font-size:9px;letter-spacing:1px;">STR %</th>
              <th style="padding:8px 12px;text-align:center;color:#64748b;font-size:9px;letter-spacing:1px;">SIGNAL</th>
            </tr>
          </thead>
          <tbody>{rows_html(bear_rows, "#b91c1c", "↓")}</tbody>
        </table>
      </div>

      <!-- Footer -->
      <div style="background:#f8f9fc;border-radius:0 0 12px 12px;padding:12px 24px;
           border-top:1px solid #e8eaf0;text-align:center;">
        <p style="font-size:10px;color:#94a3b8;margin:0;">
          AMA Gradient Backprop Engine · NIFTY 500 · Data via Yahoo Finance<br>
          <b>Not investment advice.</b> Past signals do not guarantee future performance.
        </p>
      </div>

    </div></body></html>
    """


def send_gmail_alert(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    alerts: list,
    scan_time: str,
    threshold: int,
) -> tuple[bool, str]:
    """Send HTML alert email via Gmail SMTP. Returns (success, message)."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = (
            f"⚡ AMA Signal Alert — {len(alerts)} signals ≥{threshold}%  [{scan_time}]"
        )
        msg["From"]    = sender_email
        msg["To"]      = recipient_email

        html = build_email_html(alerts, scan_time, threshold)
        msg.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True, f"Email sent to {recipient_email}"
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Authentication failed. Check Gmail address and App Password."
    except smtplib.SMTPException as e:
        return False, f"❌ SMTP error: {e}"
    except Exception as e:
        return False, f"❌ Error: {e}"



# ══════════════════════════════════════════════════════════════════════════════
# MOBILE PUSH ALERT  (ntfy.sh — free, no account needed)
# ══════════════════════════════════════════════════════════════════════════════
def send_ntfy_push(topic: str, alerts: list, scan_time: str) -> tuple[bool, str]:
    """
    Send mobile push notification via ntfy.sh.
    Install 'ntfy' app on Android / iOS and subscribe to your topic.
    Topic is just a unique string you choose — like 'ama-nifty-yourname'.
    """
    if not topic or not alerts:
        return False, "No topic or no alerts"

    bull = [a for a in alerts if a["signal"] == "BULL"]
    bear = [a for a in alerts if a["signal"] == "BEAR"]

    lines = [f"⚡ AMA VERY STRONG signals at {scan_time} IST"]
    if bull:
        lines.append("↑ BULL: " + ", ".join(
            f"{a['ticker']} {a['str']:.0f}%" for a in bull[:5]
        ))
    if bear:
        lines.append("↓ BEAR: " + ", ".join(
            f"{a['ticker']} {a['str']:.0f}%" for a in bear[:5]
        ))
    if len(alerts) > 10:
        lines.append(f"…and {len(alerts)-10} more signals")

    body  = "\n".join(lines)
    emoji = "🚀" if bull and not bear else ("⚠️" if bear and not bull else "⚡")
    title = f"{emoji} {len(bull)}↑ {len(bear)}↓ NIFTY 500 — VERY STRONG Signals"

    try:
        resp = requests.post(
            f"https://ntfy.sh/{topic.strip()}",
            data=body.encode("utf-8"),
            headers={
                "Title":    title,
                "Priority": "high",
                "Tags":     "chart_with_upwards_trend,bell",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return True, f"Push sent to ntfy topic '{topic}'"
        return False, f"ntfy error {resp.status_code}: {resp.text[:100]}"
    except requests.exceptions.ConnectionError:
        return False, "❌ No internet connection"
    except Exception as e:
        return False, f"❌ ntfy error: {e}"

# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCH
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=REFRESH_SECS, show_spinner=False)
def fetch_ticker(ticker: str, period: str, interval: str):
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


def process(ticker: str, p: dict):
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


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("results",[]),("alerts",[]),("last_scan",None),("scanned",False),
             ("email_log",[])]:
    if k not in st.session_state: st.session_state[k] = v

params = dict(
    er_len=10, fast=6, slow=7, ema_len=70,
    lookback=20, min_str=50, filt=True,
    wa=0.35, wb=0.012, wc=0.50, bd1=1.0, bd2=0.5,
    period="3mo", interval="1d",
)

# ══════════════════════════════════════════════════════════════════════════════
# NAV BAR
# ══════════════════════════════════════════════════════════════════════════════
now = datetime.now(IST)
_mins = now.hour * 60 + now.minute
mkt   = (now.weekday() < 5 and 9*60+15 <= _mins <= 15*60+30)
mkt_html = ('<span class="mkt-open">● NSE OPEN</span>' if mkt
            else '<span class="mkt-close">● NSE CLOSED</span>')

ls  = st.session_state.last_scan
nxt = ""
if ls:
    rem = max(0, REFRESH_SECS - int((now - ls).total_seconds()))
    nxt = f"Next refresh {rem//60:02d}:{rem%60:02d}"

st.markdown(f"""
<div class="nav-bar">
  <div style="display:flex;align-items:center;gap:12px;">
    <div style="width:32px;height:32px;border-radius:8px;
         background:linear-gradient(135deg,#1a1d2e,#2d3561);
         display:flex;align-items:center;justify-content:center;
         font-size:14px;color:#f59e0b;font-weight:700;">⚡</div>
    <div>
      <div class="nav-title">AMA — Gradient Backprop + Reversal Strength</div>
      <div class="nav-sub">NIFTY 500  ·  KAMA  ·  f'(x) f''(x) f'''(x)  ·  1-HR REFRESH  ·  {nxt}</div>
    </div>
  </div>
  <div class="nav-right">
    <div class="nav-badge"><span class="live-dot"></span>LIVE</div>
    <span class="nav-time">{now.strftime('%H:%M:%S  %d %b %Y')}</span>
    {mkt_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# GMAIL SETTINGS PANEL  (collapsible)
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("🔔  Alert Settings  —  Gmail + Mobile Push (ntfy)", expanded=False):
    tab_gmail, tab_push = st.tabs(["📧  Gmail Alerts", "📱  Mobile Push (ntfy)"])

    # ── ntfy tab ──────────────────────────────────────────────────────────────
    with tab_push:
        st.markdown("""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
             padding:10px 14px;margin-bottom:10px;font-size:11px;color:#1e40af;">
        <b>📱 Mobile Push via ntfy.sh — Free, no account, works on Android &amp; iOS</b><br><br>
        <b>Step 1 — Install the app:</b><br>
        &nbsp;&nbsp;• Android: <a href="https://play.google.com/store/apps/details?id=io.heckel.ntfy"
          target="_blank" style="color:#1d4ed8;">Play Store → search "ntfy"</a><br>
        &nbsp;&nbsp;• iPhone: <a href="https://apps.apple.com/app/ntfy/id1625396347"
          target="_blank" style="color:#1d4ed8;">App Store → search "ntfy"</a><br><br>
        <b>Step 2 — Choose a unique topic name</b> e.g. <code>ama-nifty-raj2024</code>
          (keep it private — anyone who knows it can subscribe)<br>
        <b>Step 3 — In the ntfy app:</b> tap ＋ → enter exactly the same topic name → Subscribe<br>
        <b>Step 4 — Enter the topic below, enable push, click Test</b><br><br>
        Alerts fire every 30 min during market hours (09:15–15:30 IST) for <b>VERY STRONG signals only (≥80%)</b>.
        </div>
        """, unsafe_allow_html=True)

        np1, np2 = st.columns([3, 1])
        with np1:
            ntfy_topic = st.text_input(
                "Your ntfy topic name",
                placeholder="ama-nifty-yourname-2024",
                key="ntfy_topic",
            )
        with np2:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            ntfy_enabled = st.toggle("Enable push", value=False, key="ntfy_enabled")
            if st.button("📱 Test Push", use_container_width=True, key="btn_test_push"):
                if ntfy_topic:
                    ok, msg = send_ntfy_push(
                        ntfy_topic,
                        [{"ticker": "RELIANCE", "signal": "BULL", "str": 91.2, "price": 2950.0},
                         {"ticker": "TCS",      "signal": "BEAR", "str": 84.7, "price": 4120.0}],
                        now.strftime("%H:%M"),
                    )
                    st.success(msg) if ok else st.error(msg)
                else:
                    st.warning("Enter a topic name first.")

    # ── Gmail tab ─────────────────────────────────────────────────────────────
    with tab_gmail:
        st.markdown("""
        <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
             padding:10px 14px;margin-bottom:12px;font-size:11px;color:#92400e;">
        <b>How to get a Gmail App Password (2 minutes):</b><br>
        1. Go to <a href="https://myaccount.google.com/security"
           target="_blank" style="color:#1d4ed8;">Google Account → Security</a><br>
        2. Enable <b>2-Step Verification</b> if not already on<br>
        3. Search <b>"App passwords"</b> → Create one for "Mail"<br>
        4. Copy the 16-character password e.g. <code>abcd efgh ijkl mnop</code>
        </div>
        """, unsafe_allow_html=True)

        gc1, gc2, gc3 = st.columns([2, 2, 1])
        with gc1:
            gmail_sender = st.text_input(
                "Your Gmail address (sender)",
                placeholder="yourname@gmail.com",
                key="gmail_sender",
            )
            gmail_password = st.text_input(
                "Gmail App Password",
                type="password",
                placeholder="abcd efgh ijkl mnop",
                key="gmail_password",
            )
        with gc2:
            gmail_recipient = st.text_input(
                "Recipient email",
                placeholder="recipient@gmail.com",
                key="gmail_recipient",
            )
            alert_threshold = st.slider(
                "Email threshold (strength %)",
                min_value=50, max_value=100, value=80, step=5,
                key="alert_threshold",
            )
        with gc3:
            st.markdown("<div style='height:26px'></div>", unsafe_allow_html=True)
            email_enabled = st.toggle("Enable email", value=False, key="email_enabled")
            if st.button("📧 Test Email", use_container_width=True, key="btn_test_email"):
                if gmail_sender and gmail_password and gmail_recipient:
                    ok, msg = send_gmail_alert(
                        gmail_sender.strip(),
                        gmail_password.replace(" ", ""),
                        gmail_recipient.strip(),
                        [{"ticker": "RELIANCE", "name": "Reliance Industries",
                          "signal": "BULL", "str": 87.5, "price": 2950.0}],
                        now.strftime("%H:%M:%S"),
                        alert_threshold,
                    )
                    st.success(msg) if ok else st.error(msg)
                else:
                    st.warning("Fill in all three email fields first.")

        if st.session_state.email_log:
            st.markdown(
                "<div style='font-size:10px;color:#64748b;margin-top:6px;'>"
                + "  ·  ".join(st.session_state.email_log[-5:])
                + "</div>",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# CONTROLS ROW
# ══════════════════════════════════════════════════════════════════════════════
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2.5, 1.5, 1.5, 1.5, 1.2, 1.2, 1, 1])
with c1:
    search = st.text_input("", placeholder="🔍  Search ticker…", label_visibility="collapsed")
with c2:
    universe = st.selectbox("", ["NIFTY 500 (All)", "NIFTY 50", "NIFTY Next 50", "Custom"],
                            label_visibility="collapsed")
with c3:
    sig_f = st.selectbox("", ["All Signals", "↑ Bull Only", "↓ Bear Only", "Strong ≥80%", "Has Signal"],
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

# ── Auto-refresh trigger (30 min during market hours only) ────────────────────
mkt_minutes_now = now.hour * 60 + now.minute
is_market_hours = (now.weekday() < 5 and 9*60+15 <= mkt_minutes_now <= 15*60+30)
elapsed = int((now - ls).total_seconds()) if ls else REFRESH_SECS + 1
if is_market_hours and elapsed >= REFRESH_SECS:
    run_btn = True
if not st.session_state.scanned:
    run_btn = True

# ══════════════════════════════════════════════════════════════════════════════
# SCAN
# ══════════════════════════════════════════════════════════════════════════════
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

    scan_time = datetime.now(IST).strftime("%H:%M:%S")

    # Build alerts above configured threshold
    thr = 80  # VERY STRONG only (>=80%)
    new_alerts = [
        {
            "ts": scan_time, "ticker": r["ticker"], "name": r["name"],
            "signal": r["signal"], "str": r["strength"], "price": r["price"],
        }
        for r in results
        if r["signal"] != "NONE" and r["strength"] >= thr  # VERY STRONG signals only
    ]

    st.session_state.alerts    = (new_alerts + st.session_state.alerts)[:100]
    st.session_state.results   = results
    st.session_state.last_scan = datetime.now(IST)
    st.session_state.scanned   = True

    # ── Send Gmail if enabled and alerts exist ─────────────────────────────────
    if (st.session_state.get("email_enabled", False)
            and new_alerts
            and st.session_state.get("gmail_sender")
            and st.session_state.get("gmail_password")
            and st.session_state.get("gmail_recipient")):
        ok, msg = send_gmail_alert(
            st.session_state.gmail_sender.strip(),
            st.session_state.gmail_password.replace(" ", ""),
            st.session_state.gmail_recipient.strip(),
            new_alerts,
            scan_time,
            thr,
        )
        log_entry = f"{scan_time}: {'✅' if ok else '❌'} {msg}"
        st.session_state.email_log = ([log_entry] + st.session_state.email_log)[:10]
        if ok:
            st.toast(f"📧 Alert email sent — {len(new_alerts)} signals", icon="✅")
        else:
            st.toast(msg, icon="❌")

    if failed:
        st.caption(
            f"⚠️ {len(failed)} tickers failed: "
            f"{', '.join(failed[:10])}{'…' if len(failed) > 10 else ''}"
        )

results = st.session_state.results

# ══════════════════════════════════════════════════════════════════════════════
# STATS BAR
# ══════════════════════════════════════════════════════════════════════════════
if results:
    n_bull = sum(1 for r in results if r["signal"] == "BULL")
    n_bear = sum(1 for r in results if r["signal"] == "BEAR")
    n_vs   = sum(1 for r in results if r["strength"] >= 80)
    n_sig  = sum(1 for r in results if r["signal"] != "NONE")
    avg_s  = np.mean([r["strength"] for r in results if r["signal"] != "NONE"] or [0])
    ls_s   = st.session_state.last_scan.strftime("%H:%M  %d %b") if st.session_state.last_scan else "—"

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

    # Alert banner (most recent)
    if st.session_state.alerts:
        a    = st.session_state.alerts[0]
        bull = a["signal"] == "BULL"
        col  = "#15803d" if bull else "#b91c1c"
        bg   = "#f0fdf4" if bull else "#fef2f2"
        st.markdown(f"""
        <div class="alert-box" style="--alert-col:{col};--alert-bg:{bg};">
          <div>
            <span style="color:{col};font-weight:700;font-size:12px;">
              {'↑' if bull else '↓'} LATEST ALERT — {a['ticker']}
            </span>
            <span style="color:#64748b;font-size:10px;margin-left:12px;">
              {a['name']}  ·  Strength {a['str']:.1f}%  ·  ₹{a['price']:,.0f}  ·  {a['ts']}
            </span>
          </div>
          <span style="color:{col};font-size:18px;font-weight:700;">{a['str']:.1f}%</span>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTER + SORT
# ══════════════════════════════════════════════════════════════════════════════
if results:
    rows = list(results)

    if search:
        s = search.upper()
        rows = [r for r in rows if s in r["ticker"] or s in r["name"].upper()]
    if sig_f == "↑ Bull Only":   rows = [r for r in rows if r["signal"] == "BULL"]
    elif sig_f == "↓ Bear Only": rows = [r for r in rows if r["signal"] == "BEAR"]
    elif sig_f == "Strong ≥80%": rows = [r for r in rows if r["strength"] >= 80]
    elif sig_f == "Has Signal":  rows = [r for r in rows if r["signal"] != "NONE"]
    if rsi_f == "OB >70":        rows = [r for r in rows if r["rsi"] >= 70]
    elif rsi_f == "OS <30":      rows = [r for r in rows if r["rsi"] <= 30]
    elif rsi_f == "Neutral":     rows = [r for r in rows if 30 < r["rsi"] < 70]

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

    # ── Table helpers ─────────────────────────────────────────────────────────
    def _chg(v):
        cls = "pos" if v >= 0 else "neg"
        return f'<span class="{cls}">{"+" if v>=0 else ""}{v:.2f}%</span>'

    def _der(v, scale=4):
        cls = "pos" if v > 0 else ("neg" if v < 0 else "neu")
        return f'<span class="{cls}">{"+" if v>0 else ""}{v:.{scale}f}</span>'

    def _rsi(v):
        cls = "rsi-ob" if v >= 70 else ("rsi-os" if v <= 30 else "rsi-n")
        return f'<span class="{cls}">{v:.1f}</span>'

    def _str(v, bull):
        if v == 0: return '<span class="neu">—</span>'
        sc = str_col(v, bull)
        return (f'<div class="str-cell">'
                f'<span class="str-num" style="color:{sc};">{v:.1f}%</span>'
                f'<div class="str-track"><div class="str-fill" style="width:{v}%;background:{sc};"></div></div>'
                f'</div>')

    def _rt(v):
        if v == 0: return '<span class="rt-vw">—</span>'
        rt, cls, _ = get_rating(v)
        return f'<span class="{cls}">{rt}</span>'

    def _sig(s):
        if s == "BULL": return '<span class="badge b-bull">↑ BULL</span>'
        if s == "BEAR": return '<span class="badge b-bear">↓ BEAR</span>'
        return '<span class="badge b-none">—</span>'

    # ── Build tbody ───────────────────────────────────────────────────────────
    tbody = ""
    for r in rows:
        bull  = r["signal"] == "BULL"
        bear  = r["signal"] == "BEAR"
        rc    = "bull-row" if bull else ("bear-row" if bear else "")
        nm    = r.get("name", "")
        tk    = r["ticker"]
        p_fmt = f"₹{r['price']:,.0f}" if r["price"] >= 100 else f"₹{r['price']:,.2f}"
        tbody += (
            f'<tr class="{rc}">'
            f'<td><span class="tk" title="{nm}">{tk}</span></td>'
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
            <th>RSI</th><th>STR %</th><th>RATING</th>
            <th class="th-sig">SIGNAL</th>
          </tr></thead>
          <tbody>{tbody}</tbody>
        </table>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer row ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    fa, fb, fc = st.columns([4, 1, 1])
    with fa:
        ls_long = (st.session_state.last_scan.strftime("%d %b %Y  %H:%M:%S")
                   if st.session_state.last_scan else "—")
        st.markdown(
            f'<div style="font-size:10px;color:#94a3b8;padding-top:6px;">'
            f'{len(rows)} rows shown  ·  {len(results)} scanned  ·  '
            f'Last scan: {ls_long}  ·  Data: Yahoo Finance  ·  Not investment advice</div>',
            unsafe_allow_html=True)
    with fb:
        df_out = pd.DataFrame([{
            "Ticker":    r["ticker"],   "Name":    r["name"],
            "Price":     round(r["price"], 2), "Chg%": round(r["chg"], 2),
            "HLC3":      r["hlc3"],    "AMA":     r["ama"],    "EMA70": r["ema70"],
            "f'(x)%":   r["d1"],      "f''(x)%": r["d2"],     "f'''(x)%": r["d3"],
            "RSI":       r["rsi"],     "Str%":    r["strength"],
            "Rating":    get_rating(r["strength"])[0] if r["signal"] != "NONE" else "—",
            "Signal":    r["signal"],  "ER":      r["er"],
        } for r in rows])
        ts = datetime.now(IST).strftime("%Y%m%d_%H%M")
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
      <div style="font-size:12px;color:#94a3b8;margin-bottom:6px;">
        Click <b style="color:#1a1d2e;">⚡ Scan</b> to fetch all equities via yfinance.
      </div>
      <div style="font-size:11px;color:#cbd5e1;">
        ~500 tickers  ·  KAMA + f'(x) f''(x) f'''(x)  ·  1-hour cache  ·  EOD data
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;color:#cbd5e1;font-size:9px;letter-spacing:1px;
     border-top:1px solid #e8eaf0;padding:10px 0;margin-top:10px;">
  AMA  ·  GRADIENT BACKPROP ENGINE  ·  NIFTY 500  ·  Yahoo Finance  ·  1-hr refresh  ·  Not investment advice
</div>
""", unsafe_allow_html=True)

# ── Auto rerun every 30 min — market hours only ───────────────────────────────
if st.session_state.last_scan:
    now_ist      = datetime.now(IST)
    mins_now     = now_ist.hour * 60 + now_ist.minute
    in_market    = (now_ist.weekday() < 5 and 9*60+15 <= mins_now <= 15*60+30)
    secs_elapsed = int((now_ist - st.session_state.last_scan).total_seconds())
    if in_market and secs_elapsed >= REFRESH_SECS:
        time.sleep(2)
        st.rerun()
