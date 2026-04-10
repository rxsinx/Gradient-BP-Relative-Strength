"""
AMA v3.0 — Gradient Backprop + Reversal Strength | NSE Full Universe Scanner
Run: streamlit run app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
import math
from datetime import datetime, timedelta
import threading
import json

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AMA Gradient Backprop — NSE",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── NSE UNIVERSE (Nifty 500 + Nifty 50 + Nifty Next 50 + midcap) ───────────
NSE_TICKERS = {
    # NIFTY 50
    "RELIANCE": "Reliance Industries",
    "TCS": "Tata Consultancy Svcs",
    "HDFCBANK": "HDFC Bank",
    "INFY": "Infosys",
    "ICICIBANK": "ICICI Bank",
    "HINDUNILVR": "Hindustan Unilever",
    "ITC": "ITC Ltd",
    "SBIN": "State Bank of India",
    "BHARTIARTL": "Bharti Airtel",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen & Toubro",
    "ASIANPAINT": "Asian Paints",
    "AXISBANK": "Axis Bank",
    "MARUTI": "Maruti Suzuki",
    "BAJFINANCE": "Bajaj Finance",
    "WIPRO": "Wipro",
    "ONGC": "ONGC",
    "NTPC": "NTPC",
    "POWERGRID": "Power Grid Corp",
    "ULTRACEMCO": "UltraTech Cement",
    "TITAN": "Titan Company",
    "SUNPHARMA": "Sun Pharmaceutical",
    "TECHM": "Tech Mahindra",
    "HCLTECH": "HCL Technologies",
    "ADANIENT": "Adani Enterprises",
    "JSWSTEEL": "JSW Steel",
    "TATAMOTORS": "Tata Motors",
    "NESTLEIND": "Nestlé India",
    "DRREDDY": "Dr Reddy's Labs",
    "DIVISLAB": "Divi's Laboratories",
    "CIPLA": "Cipla",
    "BAJAJFINSV": "Bajaj Finserv",
    "BRITANNIA": "Britannia Industries",
    "GRASIM": "Grasim Industries",
    "TATASTEEL": "Tata Steel",
    "COALINDIA": "Coal India",
    "HINDALCO": "Hindalco Industries",
    "HEROMOTOCO": "Hero MotoCorp",
    "EICHERMOT": "Eicher Motors",
    "SHREECEM": "Shree Cement",
    "APOLLOHOSP": "Apollo Hospitals",
    "BPCL": "BPCL",
    "INDUSINDBK": "IndusInd Bank",
    "M&M": "Mahindra & Mahindra",
    "TATACONSUM": "Tata Consumer Products",
    "PIDILITIND": "Pidilite Industries",
    "HAVELLS": "Havells India",
    "DABUR": "Dabur India",
    "SIEMENS": "Siemens India",
    "ADANIPORTS": "Adani Ports",
    # NIFTY NEXT 50
    "BAJAJ-AUTO": "Bajaj Auto",
    "BANKBARODA": "Bank of Baroda",
    "BERGEPAINT": "Berger Paints",
    "BIOCON": "Biocon",
    "BOSCHLTD": "Bosch",
    "CHOLAFIN": "Cholamandalam Finance",
    "COLPAL": "Colgate-Palmolive",
    "CONCOR": "Container Corp",
    "CUMMINSIND": "Cummins India",
    "DLF": "DLF",
    "GLAND": "Gland Pharma",
    "GODREJCP": "Godrej Consumer Products",
    "GODREJPROP": "Godrej Properties",
    "HAL": "Hindustan Aeronautics",
    "ICICIPRULI": "ICICI Prudential Life",
    "INDUSTOWER": "Indus Towers",
    "IRCTC": "IRCTC",
    "LTF": "L&T Finance",
    "LUPIN": "Lupin",
    "MARICO": "Marico",
    "MCDOWELL-N": "United Spirits",
    "MPHASIS": "Mphasis",
    "NAUKRI": "Info Edge",
    "NHPC": "NHPC",
    "NMDC": "NMDC",
    "OFSS": "Oracle Financial Services",
    "PAGEIND": "Page Industries",
    "PEL": "Piramal Enterprises",
    "PETRONET": "Petronet LNG",
    "PIIND": "PI Industries",
    "POLYCAB": "Polycab India",
    "RECLTD": "REC Ltd",
    "SBICARD": "SBI Cards",
    "SBILIFE": "SBI Life Insurance",
    "SRF": "SRF",
    "TORNTPHARM": "Torrent Pharmaceuticals",
    "TRENT": "Trent",
    "UBL": "United Breweries",
    "VEDL": "Vedanta",
    "VOLTAS": "Voltas",
    "ZOMATO": "Zomato",
    "PAYTM": "Paytm",
    "NYKAA": "Nykaa",
    "POLICYBZR": "PB Fintech",
    # MIDCAP SELECT
    "ABCAPITAL": "Aditya Birla Capital",
    "ABFRL": "Aditya Birla Fashion",
    "ACC": "ACC Ltd",
    "AIAENG": "AIA Engineering",
    "ALKEM": "Alkem Laboratories",
    "AMBUJACEM": "Ambuja Cements",
    "APLAPOLLO": "APL Apollo Tubes",
    "ASTRAL": "Astral Ltd",
    "ATUL": "Atul Ltd",
    "AUBANK": "AU Small Finance Bank",
    "BALKRISIND": "Balkrishna Industries",
    "BATAINDIA": "Bata India",
    "BEL": "Bharat Electronics",
    "BHARATFORG": "Bharat Forge",
    "BHEL": "BHEL",
    "CANBK": "Canara Bank",
    "CANFINHOME": "Can Fin Homes",
    "CDSL": "CDSL",
    "COFORGE": "Coforge",
    "COROMANDEL": "Coromandel International",
    "CROMPTON": "Crompton Greaves Consumer",
    "CSBBANK": "CSB Bank",
    "DALBHARAT": "Dalmia Bharat",
    "DEEPAKNTR": "Deepak Nitrite",
    "DIXON": "Dixon Technologies",
    "EDELWEISS": "Edelweiss Financial",
    "ELGIEQUIP": "Elgi Equipments",
    "EMAMILTD": "Emami",
    "ESCORTS": "Escorts Kubota",
    "EXIDEIND": "Exide Industries",
    "FEDERALBNK": "Federal Bank",
    "FORCEMOT": "Force Motors",
    "FSL": "Firstsource Solutions",
    "GAIL": "GAIL India",
    "GLENMARK": "Glenmark Pharma",
    "GLAXO": "GSK Pharma India",
    "GMRINFRA": "GMR Airports Infra",
    "GNFC": "GNFC",
    "GODFRYPHLP": "Godfrey Phillips",
    "GPPL": "Gujarat Pipavav Port",
    "GRINDWELL": "Grindwell Norton",
    "GSPL": "Gujarat State Petronet",
    "HAPPSTMNDS": "Happiest Minds",
    "HINDPETRO": "HPCL",
    "HONAUT": "Honeywell Automation",
    "IDFCFIRSTB": "IDFC First Bank",
    "IEX": "Indian Energy Exchange",
    "IPCALAB": "IPCA Laboratories",
    "JKCEMENT": "JK Cement",
    "JKPAPER": "JK Paper",
    "JUBLFOOD": "Jubilant Foodworks",
    "KAJARIACER": "Kajaria Ceramics",
    "KANSAINER": "Kansai Nerolac",
    "KEC": "KEC International",
    "KPITTECH": "KPIT Technologies",
    "LALPATHLAB": "Dr Lal PathLabs",
    "LAURUSLABS": "Laurus Labs",
    "LICHSGFIN": "LIC Housing Finance",
    "LINDEINDIA": "Linde India",
    "LTTS": "L&T Technology Services",
    "LUXIND": "Lux Industries",
    "M&MFIN": "M&M Financial Services",
    "MANAPPURAM": "Manappuram Finance",
    "MARICO": "Marico",
    "MFSL": "Max Financial Services",
    "MINDTREE": "LTIMindtree",
    "MOTILALOFS": "Motilal Oswal Financial",
    "MRF": "MRF",
    "MUTHOOTFIN": "Muthoot Finance",
    "NATCOPHARM": "Natco Pharma",
    "NAVINFLUOR": "Navin Fluorine",
    "NBCC": "NBCC",
    "NLCINDIA": "NLC India",
    "OBEROIRLTY": "Oberoi Realty",
    "PERSISTENT": "Persistent Systems",
    "PFC": "Power Finance Corp",
    "PHOENIXLTD": "Phoenix Mills",
    "PNBHOUSING": "PNB Housing Finance",
    "PRAJIND": "Praj Industries",
    "PRINCEPIPE": "Prince Pipes",
    "PURVA": "Puravankara",
    "RAJRATAN": "Rajratan Global Wire",
    "RAJESHEXPO": "Rajesh Exports",
    "RAYMOND": "Raymond",
    "RELAXO": "Relaxo Footwears",
    "RITES": "RITES",
    "SANOFI": "Sanofi India",
    "SAPPHIRE": "Sapphire Foods",
    "SCHAEFFLER": "Schaeffler India",
    "SKFINDIA": "SKF India",
    "SOBHA": "Sobha",
    "SOLARA": "Solara Active Pharma",
    "SPARC": "Sun Pharma Advanced",
    "STLTECH": "Sterlite Technologies",
    "SUPPETRO": "Supreme Petrochem",
    "SUPREMEIND": "Supreme Industries",
    "SUVENPHAR": "Suven Pharmaceuticals",
    "TANLA": "Tanla Platforms",
    "TATACHEM": "Tata Chemicals",
    "TATACOMM": "Tata Communications",
    "TATAELXSI": "Tata Elxsi",
    "TEJASNET": "Tejas Networks",
    "THERMAX": "Thermax",
    "TIMKEN": "Timken India",
    "TORNTPOWER": "Torrent Power",
    "TTKPRESTIG": "TTK Prestige",
    "TVSHLTD": "TVS Holdings",
    "TVSMOTOR": "TVS Motor",
    "UPL": "UPL",
    "VAIBHAVGBL": "Vaibhav Global",
    "VGUARD": "V-Guard Industries",
    "VINATIORGA": "Vinati Organics",
    "VMART": "V-Mart Retail",
    "WOCKPHARMA": "Wockhardt",
    "ZEEL": "Zee Entertainment",
    "ZENSARTECH": "Zensar Technologies",
}

YF_SUFFIX = ".NS"

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Space+Grotesk:wght@300;400;500;600&display=swap');

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #08080f !important;
    color: #d0d0e0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
[data-testid="stSidebar"] {
    background: #0c0c18 !important;
    border-right: 1px solid #1a1a2e;
}
[data-testid="stHeader"] { background: transparent !important; }
.stApp { background: #08080f !important; }

/* ── Top header bar ── */
.ama-header {
    background: linear-gradient(135deg, #0d0d1f 0%, #0a0a18 100%);
    border: 1px solid #1e1e3e;
    border-radius: 6px;
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.ama-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    color: #ffd700;
    letter-spacing: 3px;
    text-transform: uppercase;
}
.ama-subtitle { font-size: 9px; color: #556; letter-spacing: 2px; margin-top: 2px; }
.live-indicator {
    display: flex; align-items: center; gap: 8px;
    font-size: 10px; color: #00ff41; letter-spacing: 2px;
}
.live-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #00ff41;
    box-shadow: 0 0 6px #00ff41;
    animation: pulse 1.2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.8)} }

/* ── Metric cards ── */
.metric-card {
    background: #0d0d1a;
    border: 1px solid #1a1a2e;
    border-radius: 5px;
    padding: 10px 14px;
    text-align: center;
}
.metric-label { font-size: 8px; color: #556; letter-spacing: 2px; text-transform: uppercase; }
.metric-val { font-size: 20px; font-weight: 700; margin-top: 2px; }
.val-bull { color: #00ff41; }
.val-bear { color: #ff2e2e; }
.val-gold { color: #ffd700; }
.val-cyan { color: #00e5ff; }
.val-amber { color: #ffc107; }
.val-muted { color: #556; }

/* ── Section headers ── */
.section-hdr {
    font-size: 9px; letter-spacing: 3px; color: #00e5ff;
    text-transform: uppercase; border-bottom: 1px solid #1a1a2e;
    padding-bottom: 4px; margin: 10px 0 8px;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Signal table ── */
.sig-table { width: 100%; border-collapse: collapse; font-size: 10px; }
.sig-table th {
    background: #0c0c1a; color: #334; font-size: 8px; letter-spacing: 2px;
    padding: 6px 8px; text-align: left; border-bottom: 1px solid #1a1a2e;
    position: sticky; top: 0;
}
.sig-table td { padding: 5px 8px; border-bottom: 1px solid #0f0f1a; }
.sig-row-bull { background: rgba(0,255,65,0.03); }
.sig-row-bear { background: rgba(255,46,46,0.03); }
.ticker-cell { color: #ffd700; font-weight: 700; font-size: 10px; }
.price-cell { color: #c0c0d0; }
.chg-pos { color: #00ff41; }
.chg-neg { color: #ff2e2e; }
.badge {
    display: inline-block; padding: 2px 7px; border-radius: 3px;
    font-size: 8px; font-weight: 700; letter-spacing: 1px;
}
.badge-bull { background: #0a1f0a; color: #00ff41; border: 1px solid #1a3a1a; }
.badge-bear { background: #1f0a0a; color: #ff2e2e; border: 1px solid #3a1a1a; }
.badge-none { background: #111; color: #445; border: 1px solid #1a1a2e; }

/* ── Strength meter ── */
.str-bar-bg { background: #111; border-radius: 2px; height: 5px; width: 100%; margin-top: 2px; }
.str-bar { height: 5px; border-radius: 2px; }

/* ── Detail cards ── */
.detail-card {
    background: #0d0d1a; border: 1px solid #1a1a2e;
    border-radius: 5px; padding: 12px 14px; margin-bottom: 8px;
}
.detail-card .section-hdr { margin-top: 0; }

/* ── Derivative row ── */
.deriv-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 3px 0; border-bottom: 1px solid #0f0f1a; font-size: 10px;
}
.deriv-label { color: #556; }
.deriv-pos { color: #00ff41; font-weight: 700; }
.deriv-neg { color: #ff2e2e; font-weight: 700; }
.deriv-neu { color: #00e5ff; font-weight: 700; }

/* ── Alert history ── */
.alert-entry {
    background: #0d0d1a; border: 1px solid #1a1a2e;
    border-radius: 4px; padding: 8px 12px; margin-bottom: 5px;
    display: flex; justify-content: space-between; align-items: center;
}
.alert-bull-entry { border-left: 3px solid #00ff41; }
.alert-bear-entry { border-left: 3px solid #ff2e2e; }
.alert-time { color: #445; font-size: 9px; }
.alert-sym { font-weight: 700; font-size: 10px; }
.alert-str { font-size: 12px; font-weight: 700; }

/* ── Strength gauge colors ── */
.gauge-vs { color: #00ff41; }
.gauge-s { color: #90ee90; }
.gauge-m { color: #ffc107; }
.gauge-w { color: #ffa500; }
.gauge-vw { color: #445; }

/* ── Progress bars (streamlit override) ── */
.stProgress > div > div > div > div { background: #00e5ff !important; }

/* ── Sidebar styling ── */
.sidebar-section {
    background: #0d0d1a; border: 1px solid #1a1a2e; border-radius: 5px;
    padding: 10px 12px; margin-bottom: 10px;
}
.sidebar-label {
    font-size: 8px; letter-spacing: 2px; color: #556;
    text-transform: uppercase; margin-bottom: 6px;
}

/* ── Scrollable container ── */
.scroll-table { max-height: 680px; overflow-y: auto; }
.scroll-table::-webkit-scrollbar { width: 4px; }
.scroll-table::-webkit-scrollbar-thumb { background: #1a1a2e; border-radius: 2px; }

/* ── Rating badge ── */
.rating-vs { background:#0a1f0a;color:#00ff41;border:1px solid #1a3a1a; }
.rating-s  { background:#0f1f0f;color:#90ee90;border:1px solid #1a3a1a; }
.rating-m  { background:#1f1a00;color:#ffc107;border:1px solid #3a3000; }
.rating-w  { background:#1f1200;color:#ffa500;border:1px solid #3a2000; }
.rating-vw { background:#111;color:#445;border:1px solid #1a1a2e; }

/* ── Streamlit widget overrides ── */
.stSelectbox > div, .stMultiSelect > div { background: #0d0d1a !important; }
label { color: #778 !important; font-size: 10px !important; letter-spacing: 1px !important; }
.stSlider > div > div > div { background: #00e5ff !important; }
div[data-testid="stMetricValue"] { color: #00e5ff !important; }
.stButton > button {
    background: #0d0d1a !important; border: 1px solid #1a1a2e !important;
    color: #00e5ff !important; font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 1px !important;
    border-radius: 4px !important;
}
.stButton > button:hover { border-color: #00e5ff !important; background: #0a1a2a !important; }
</style>
""", unsafe_allow_html=True)


# ─── MATH ENGINE ─────────────────────────────────────────────────────────────

def calc_kama(prices: np.ndarray, er_len: int = 10,
              fast_period: int = 6, slow_period: int = 7) -> np.ndarray:
    fast_sc = 2.0 / (fast_period + 1)
    slow_sc = 2.0 / (slow_period + 1)
    n = len(prices)
    ama = np.full(n, np.nan)
    ama[0] = prices[0]
    for i in range(1, n):
        if i < er_len:
            ama[i] = prices[i]
            continue
        direction = abs(prices[i] - prices[i - er_len])
        volatility = np.sum(np.abs(np.diff(prices[i - er_len: i + 1])))
        er = direction / volatility if volatility != 0 else 0.0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        ama[i] = ama[i - 1] + sc * (prices[i] - ama[i - 1])
    return ama


def calc_derivatives(ama: np.ndarray) -> tuple:
    n = len(ama)
    d1 = np.zeros(n)
    d2 = np.zeros(n)
    d3 = np.zeros(n)
    for i in range(1, n):
        if ama[i] != 0 and not np.isnan(ama[i]):
            d1[i] = ((ama[i] - ama[i - 1]) / ama[i]) * 100.0
    for i in range(2, n):
        if ama[i] != 0 and not np.isnan(ama[i]):
            d2[i] = ((d1[i] - d1[i - 1]) / ama[i]) * 10000.0
    for i in range(3, n):
        if ama[i] != 0 and not np.isnan(ama[i]):
            d3[i] = ((d2[i] - d2[i - 1]) / ama[i]) * 1_000_000.0
    return d1, d2, d3


def calc_er(prices: np.ndarray, er_len: int) -> np.ndarray:
    n = len(prices)
    er = np.zeros(n)
    for i in range(er_len, n):
        direction = abs(prices[i] - prices[i - er_len])
        vol = np.sum(np.abs(np.diff(prices[i - er_len: i + 1])))
        er[i] = direction / vol if vol != 0 else 0.0
    return er


def compute_gradient_signal(d1, d2, d3, ama, lookback=20,
                             w_accel=0.35, w_div=0.012, w_jerk=0.5,
                             boost_d1=1.0, boost_d2=0.5,
                             deriv_order=3):
    """
    Full Pine Script equivalent: gradient flow detection + reversal strength.
    Returns dict with all signal components.
    """
    n = len(d1)
    i = n - 1  # latest bar

    d1v, d2v, d3v = d1[i], d2[i], d3[i]

    # Gradient flow detection
    gf_bull = (d2v > 0 and d1v < 0)
    gf_bear = (d2v < 0 and d1v > 0)
    if deriv_order >= 3:
        gf_bull = gf_bull or (d3v > 0 and d2v < 0 and d1v < 0)
        gf_bear = gf_bear or (d3v < 0 and d2v > 0 and d1v > 0)

    strength = 0.0
    c1 = c2 = c3 = raw_str = max_str = 0.0
    boost_applied = False

    if gf_bull or gf_bear:
        c1 = abs(d2v)
        c2 = abs(d1v) * abs(d2v)
        c3 = abs(d3v) * 0.1 if deriv_order >= 3 else 0.0
        raw_str = (c1 * w_accel) + (c2 * w_div) + (c3 * w_jerk)

        lb_start = max(0, i - lookback)
        d2_window = np.abs(d2[lb_start:i + 1])
        d1_window = np.abs(d1[lb_start:i + 1])
        d3_window = np.abs(d3[lb_start:i + 1]) * 0.1

        max_accel = np.max(d2_window) if len(d2_window) > 0 else 0
        max_div   = np.max(d1_window * np.abs(d2[lb_start:i + 1])) if len(d2_window) > 0 else 0
        max_jerk  = np.max(d3_window) if deriv_order >= 3 and len(d3_window) > 0 else 0

        max_str = max(0.0001,
                      (max_accel * w_accel) + (max_div * w_div) + (max_jerk * w_jerk))
        strength = min(100.0, (raw_str / max_str) * 100.0)

        if abs(d1v) > boost_d1 and abs(d2v) > boost_d2:
            strength = min(100.0, strength * 1.25)
            boost_applied = True

    return {
        "d1": d1v, "d2": d2v, "d3": d3v,
        "gf_bull": gf_bull, "gf_bear": gf_bear,
        "strength": round(strength, 1),
        "c1": c1, "c2": c2, "c3": c3,
        "raw_str": raw_str, "max_str": max_str,
        "boost": boost_applied,
    }


def get_rating(strength: float) -> tuple[str, str]:
    if strength >= 80:  return "VERY STRONG", "gauge-vs"
    if strength >= 60:  return "STRONG",      "gauge-s"
    if strength >= 40:  return "MODERATE",    "gauge-m"
    if strength >= 20:  return "WEAK",        "gauge-w"
    return "VERY WEAK", "gauge-vw"


def get_bar_color(strength: float, bull: bool) -> str:
    if strength >= 80: return "#00ff41" if bull else "#ff2e2e"
    if strength >= 60: return "#90ee90" if bull else "#ff7070"
    if strength >= 40: return "#ffc107"
    return "#ffa500"


# ─── DATA FETCH ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def fetch_ohlc(ticker: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    try:
        df = yf.download(f"{ticker}{YF_SUFFIX}", period=period,
                         interval=interval, progress=False, auto_adjust=True)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.dropna(subset=["Close"])
        if hasattr(df.columns, "levels"):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return pd.DataFrame()


def process_ticker(ticker: str, params: dict) -> dict | None:
    df = fetch_ohlc(ticker, period=params["period"], interval=params["interval"])
    if df.empty or len(df) < params["er_len"] + 5:
        return None

    hlc3 = ((df["High"] + df["Low"] + df["Close"]) / 3).values
    close = df["Close"].values

    ama = calc_kama(hlc3, er_len=params["er_len"],
                    fast_period=params["fast_period"],
                    slow_period=params["slow_period"])
    er  = calc_er(hlc3, params["er_len"])
    d1, d2, d3 = calc_derivatives(ama)

    sig = compute_gradient_signal(
        d1, d2, d3, ama,
        lookback=params["lookback"],
        w_accel=params["w_accel"],
        w_div=params["w_div"],
        w_jerk=params["w_jerk"],
        boost_d1=params["boost_d1"],
        boost_d2=params["boost_d2"],
        deriv_order=params["deriv_order"],
    )

    price  = float(close[-1])
    prev   = float(close[-2]) if len(close) > 1 else price
    chg_pct = ((price - prev) / prev * 100) if prev != 0 else 0.0

    signal = "NONE"
    if params["strength_filter"]:
        if sig["gf_bull"] and sig["strength"] >= params["min_strength"]:
            signal = "BULL"
        elif sig["gf_bear"] and sig["strength"] >= params["min_strength"]:
            signal = "BEAR"
    else:
        if sig["gf_bull"]:  signal = "BULL"
        elif sig["gf_bear"]: signal = "BEAR"

    ema70 = pd.Series(close).ewm(span=70, adjust=False).mean().iloc[-1]

    return {
        "ticker": ticker,
        "name": NSE_TICKERS.get(ticker, ticker),
        "price": price,
        "prev_price": prev,
        "chg_pct": chg_pct,
        "ama": float(ama[-1]) if not np.isnan(ama[-1]) else price,
        "ema70": float(ema70),
        "er": float(er[-1]),
        "signal": signal,
        **sig,
        # Keep arrays for chart
        "ama_series": ama[-60:].tolist(),
        "price_series": close[-60:].tolist(),
        "d1_series": d1[-60:].tolist(),
        "d2_series": d2[-60:].tolist(),
        "d3_series": d3[-60:].tolist(),
        "dates": [str(d.date()) for d in df.index[-60:]],
    }


@st.cache_data(ttl=60, show_spinner=False)
def scan_all_tickers(tickers: list, params_json: str) -> list:
    params = json.loads(params_json)
    results = []
    for ticker in tickers:
        r = process_ticker(ticker, params)
        if r:
            results.append(r)
    return results


# ─── STATE ───────────────────────────────────────────────────────────────────

if "alert_history" not in st.session_state:
    st.session_state.alert_history = []
if "last_scan" not in st.session_state:
    st.session_state.last_scan = None
if "results" not in st.session_state:
    st.session_state.results = []
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = "RELIANCE"


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="section-hdr">⚙ SCAN PARAMETERS</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Universe</div>', unsafe_allow_html=True)
    scan_mode = st.radio("", ["All NSE (~150)", "Nifty 50 Only", "Custom"],
                         index=0, label_visibility="collapsed")
    if scan_mode == "Nifty 50 Only":
        NIFTY50 = list(NSE_TICKERS.keys())[:50]
        scan_tickers = NIFTY50
    elif scan_mode == "Custom":
        custom = st.multiselect("Select tickers", list(NSE_TICKERS.keys()),
                                default=["RELIANCE", "TCS", "INFY", "HDFCBANK"])
        scan_tickers = custom or list(NSE_TICKERS.keys())[:50]
    else:
        scan_tickers = list(NSE_TICKERS.keys())

    st.divider()
    st.markdown('<div class="section-hdr">📊 AMA CORE</div>', unsafe_allow_html=True)
    er_len       = st.slider("ER Window", 3, 30, 10)
    fast_period  = st.slider("Fast SC Period", 2, 10, 6)
    slow_period  = st.slider("Slow SC Period", 5, 15, 7)
    ema_len      = st.slider("EMA Length", 20, 200, 70)
    deriv_order  = st.select_slider("Derivative Order", [1, 2, 3], 3)

    st.divider()
    st.markdown('<div class="section-hdr">🔍 REVERSAL STRENGTH</div>', unsafe_allow_html=True)
    lookback       = st.slider("Strength Lookback", 5, 50, 20)
    min_strength   = st.slider("Min Signal Strength %", 0, 100, 50, step=5)
    strength_filter = st.toggle("Enable Strength Filter", True)
    w_accel        = st.slider("Weight: Accel (C1)", 0.1, 1.0, 0.35, step=0.05)
    w_div          = st.slider("Weight: Divergence (C2)", 0.001, 0.05, 0.012, step=0.001)
    w_jerk         = st.slider("Weight: Jerk (C3)", 0.1, 1.0, 0.5, step=0.05)
    boost_d1       = st.slider("Boost Threshold |f'|", 0.5, 3.0, 1.0, step=0.1)
    boost_d2       = st.slider("Boost Threshold |f''|", 0.1, 2.0, 0.5, step=0.1)

    st.divider()
    st.markdown('<div class="section-hdr">📅 DATA</div>', unsafe_allow_html=True)
    period   = st.selectbox("History Period", ["1mo", "3mo", "6mo", "1y", "2y"], index=1)
    interval = st.selectbox("Bar Interval", ["1d", "1wk"], index=0)

    st.divider()
    st.markdown('<div class="section-hdr">🔔 ALERTS</div>', unsafe_allow_html=True)
    alert_threshold = st.slider("Alert Threshold %", 50, 100, 80, step=5)
    auto_refresh    = st.toggle("Auto Refresh (60s)", False)

    st.divider()
    scan_btn = st.button("⚡  RUN SCAN", use_container_width=True)

# ─── PARAMS DICT ─────────────────────────────────────────────────────────────
params = dict(
    er_len=er_len, fast_period=fast_period, slow_period=slow_period,
    ema_len=ema_len, deriv_order=deriv_order, lookback=lookback,
    min_strength=min_strength, strength_filter=strength_filter,
    w_accel=w_accel, w_div=w_div, w_jerk=w_jerk,
    boost_d1=boost_d1, boost_d2=boost_d2,
    period=period, interval=interval,
)
params_json = json.dumps(params)


# ─── HEADER ──────────────────────────────────────────────────────────────────
now_str = datetime.now().strftime("%H:%M:%S  |  %d %b %Y")
market_open = (
    datetime.now().weekday() < 5 and
    (9 * 60 + 15) <= (datetime.now().hour * 60 + datetime.now().minute) <= (15 * 60 + 30)
)
mkt_color  = "#00ff41" if market_open else "#ff2e2e"
mkt_label  = "MARKET OPEN" if market_open else "MARKET CLOSED"

st.markdown(f"""
<div class="ama-header">
  <div>
    <div class="ama-title">⚡ AMA v3.0 — Gradient Backprop + Reversal Strength</div>
    <div class="ama-subtitle">NSE FULL UNIVERSE SCANNER  ◈  KAMA + MULTI-ORDER DERIVATIVES + BACKPROPAGATION SIGNAL ENGINE</div>
  </div>
  <div style="text-align:right;">
    <div class="live-indicator"><span class="live-dot"></span> LIVE &nbsp;|&nbsp; {now_str}</div>
    <div style="font-size:9px;color:{mkt_color};letter-spacing:2px;margin-top:3px;">{mkt_label}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
if auto_refresh:
    last = st.session_state.last_scan
    if last is None or (datetime.now() - last).seconds >= 60:
        scan_btn = True


# ─── SCAN ─────────────────────────────────────────────────────────────────────
if scan_btn or not st.session_state.results:
    with st.spinner(f"Scanning {len(scan_tickers)} NSE equities via yfinance..."):
        prog = st.progress(0, text="Initializing scan...")
        results = []
        for idx, ticker in enumerate(scan_tickers):
            prog.progress((idx + 1) / len(scan_tickers),
                          text=f"Processing {ticker}... ({idx+1}/{len(scan_tickers)})")
            r = process_ticker(ticker, params)
            if r:
                results.append(r)

        prog.empty()
        st.session_state.results = results
        st.session_state.last_scan = datetime.now()

        # Generate alerts for signals above alert_threshold
        for r in results:
            if r["signal"] != "NONE" and r["strength"] >= alert_threshold:
                entry = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "ticker": r["ticker"],
                    "name": r["name"],
                    "signal": r["signal"],
                    "strength": r["strength"],
                    "price": r["price"],
                }
                existing = [a["ticker"] for a in st.session_state.alert_history[:10]]
                if r["ticker"] not in existing:
                    st.session_state.alert_history.insert(0, entry)
        st.session_state.alert_history = st.session_state.alert_history[:50]

results = st.session_state.results


# ─── SUMMARY METRICS ─────────────────────────────────────────────────────────
if results:
    bull_count  = sum(1 for r in results if r["signal"] == "BULL")
    bear_count  = sum(1 for r in results if r["signal"] == "BEAR")
    vs_count    = sum(1 for r in results if r["strength"] >= 80)
    avg_str     = np.mean([r["strength"] for r in results if r["signal"] != "NONE"] or [0])

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">SCANNED</div>
          <div class="metric-val val-cyan">{len(results)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">↑ BULL SIGNALS</div>
          <div class="metric-val val-bull">{bull_count}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">↓ BEAR SIGNALS</div>
          <div class="metric-val val-bear">{bear_count}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">VERY STRONG ≥80%</div>
          <div class="metric-val val-gold">{vs_count}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-label">AVG SIGNAL STR</div>
          <div class="metric-val val-amber">{avg_str:.1f}%</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# ─── ALERT BANNER ─────────────────────────────────────────────────────────────
if st.session_state.alert_history:
    a = st.session_state.alert_history[0]
    bull = a["signal"] == "BULL"
    color = "#00ff41" if bull else "#ff2e2e"
    arrow = "↑" if bull else "↓"
    rating, _ = get_rating(a["strength"])
    st.markdown(f"""
    <div style="background:#0d0d0a;border:1px solid {'#1a3a1a' if bull else '#3a1a1a'};
         border-left:4px solid {color};border-radius:4px;padding:8px 16px;margin-bottom:8px;
         display:flex;justify-content:space-between;align-items:center;">
      <div>
        <span style="color:{color};font-weight:700;font-size:10px;">
          {arrow} {a['signal']} ALERT — {a['ticker']} ({a['name']})
        </span>
        <span style="color:#556;font-size:9px;margin-left:12px;">{rating} — ₹{a['price']:,.0f} — {a['time']}</span>
      </div>
      <span style="color:{color};font-size:16px;font-weight:700;">{a['strength']:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)


# ─── MAIN LAYOUT ──────────────────────────────────────────────────────────────
left_col, right_col = st.columns([5, 4], gap="small")

# ── LEFT: Signal table ────────────────────────────────────────────────────────
with left_col:
    st.markdown('<div class="section-hdr">📡 NSE SIGNAL SCANNER</div>', unsafe_allow_html=True)

    # Filter controls
    fc1, fc2, fc3 = st.columns([2, 1, 1])
    with fc1:
        search = st.text_input("", placeholder="Search ticker / name...",
                               label_visibility="collapsed", key="search")
    with fc2:
        sig_filter = st.selectbox("", ["All", "Bull Only", "Bear Only", "Strong (≥80%)"],
                                  label_visibility="collapsed", key="sf")
    with fc3:
        sort_by = st.selectbox("", ["Strength ↓", "Price ↓", "Change %", "Ticker A-Z"],
                               label_visibility="collapsed", key="sb")

    if results:
        filtered = [r for r in results]

        # Search filter
        if search:
            s = search.upper()
            filtered = [r for r in filtered
                        if s in r["ticker"] or s in r["name"].upper()]

        # Signal filter
        if sig_filter == "Bull Only":
            filtered = [r for r in filtered if r["signal"] == "BULL"]
        elif sig_filter == "Bear Only":
            filtered = [r for r in filtered if r["signal"] == "BEAR"]
        elif sig_filter == "Strong (≥80%)":
            filtered = [r for r in filtered if r["strength"] >= 80]

        # Sort
        if sort_by == "Strength ↓":
            filtered.sort(key=lambda x: (x["signal"] != "NONE", x["strength"]), reverse=True)
        elif sort_by == "Price ↓":
            filtered.sort(key=lambda x: x["price"], reverse=True)
        elif sort_by == "Change %":
            filtered.sort(key=lambda x: abs(x["chg_pct"]), reverse=True)
        elif sort_by == "Ticker A-Z":
            filtered.sort(key=lambda x: x["ticker"])

        # Table
        rows_html = ""
        for r in filtered:
            bull  = r["signal"] == "BULL"
            bear  = r["signal"] == "BEAR"
            none  = r["signal"] == "NONE"
            chg_c = "chg-pos" if r["chg_pct"] >= 0 else "chg-neg"
            chg_s = ("+" if r["chg_pct"] >= 0 else "") + f"{r['chg_pct']:.2f}%"
            bclass = "badge-bull" if bull else ("badge-bear" if bear else "badge-none")
            btxt   = ("↑ BULL" if bull else ("↓ BEAR" if bear else "—"))

            price_disp = f"₹{r['price']:,.0f}" if r["price"] >= 100 else f"₹{r['price']:,.2f}"
            str_color  = get_bar_color(r["strength"], bull)

            # Strength bar
            bar_w = r["strength"]
            bar_html = f"""
            <div class="str-bar-bg">
              <div class="str-bar" style="width:{bar_w}%;background:{str_color}"></div>
            </div>"""

            row_cls = "sig-row-bull" if bull else ("sig-row-bear" if bear else "")
            sel_style = "border-left:2px solid #00e5ff;" if r["ticker"] == st.session_state.selected_ticker else ""

            rating, _ = get_rating(r["strength"])
            str_disp = f"{r['strength']:.1f}%" if r["signal"] != "NONE" else "—"

            rows_html += f"""
            <tr class="{row_cls}" style="cursor:pointer;{sel_style}">
              <td class="ticker-cell">{r['ticker']}</td>
              <td class="price-cell" style="font-size:9px;color:#778;max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{r['name'][:18]}</td>
              <td class="price-cell">{price_disp}</td>
              <td class="{chg_c}">{chg_s}</td>
              <td><span class="badge {bclass}">{btxt}</span></td>
              <td style="min-width:80px;">
                <div style="display:flex;align-items:center;gap:5px;">
                  <span style="color:{str_color if r['signal']!='NONE' else '#445'};font-weight:700;font-size:10px;min-width:35px;">{str_disp}</span>
                  {bar_html if r['signal']!='NONE' else ''}
                </div>
              </td>
              <td style="font-size:8px;color:#556;">{rating if r['signal']!='NONE' else '—'}</td>
            </tr>"""

        st.markdown(f"""
        <div class="scroll-table">
        <table class="sig-table">
          <thead>
            <tr>
              <th>TICKER</th><th>NAME</th><th>PRICE</th>
              <th>CHG %</th><th>SIGNAL</th><th>STRENGTH</th><th>RATING</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)

        # Quick-select
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        sel_options = [r["ticker"] for r in filtered]
        if sel_options:
            sel_idx = sel_options.index(st.session_state.selected_ticker) \
                      if st.session_state.selected_ticker in sel_options else 0
            chosen = st.selectbox("Select ticker for detail view →",
                                  sel_options, index=sel_idx,
                                  format_func=lambda t: f"{t}  —  {NSE_TICKERS.get(t, t)}")
            st.session_state.selected_ticker = chosen
    else:
        st.info("Click **RUN SCAN** to start scanning NSE equities.")


# ── RIGHT: Detail + Alerts ────────────────────────────────────────────────────
with right_col:
    sel = st.session_state.selected_ticker
    sel_data = next((r for r in results if r["ticker"] == sel), None)

    if sel_data:
        r = sel_data
        bull = r["signal"] == "BULL"
        bear = r["signal"] == "BEAR"
        price_color = "#00ff41" if r["chg_pct"] >= 0 else "#ff2e2e"
        chg_sign    = "+" if r["chg_pct"] >= 0 else ""
        rating, rating_cls = get_rating(r["strength"])

        # ── Header ────────────────────────────────────────────────────────────
        st.markdown(f"""
        <div class="detail-card" style="border-left:3px solid {'#00ff41' if bull else ('#ff2e2e' if bear else '#1a1a2e')}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
              <span style="color:#ffd700;font-size:16px;font-weight:700;">{r['ticker']}</span>
              <span style="color:#556;font-size:10px;margin-left:8px;">{r['name']}</span><br>
              <span style="color:#445;font-size:9px;">NSE  ◈  KAMA={r['ama']:.2f}  ◈  EMA70={r['ema70']:.2f}  ◈  ER={r['er']:.4f}</span>
            </div>
            <div style="text-align:right;">
              <div style="color:{price_color};font-size:18px;font-weight:700;">
                ₹{r['price']:,.0f if r['price'] >= 100 else ',.2f'}
              </div>
              <div style="color:{price_color};font-size:10px;">{chg_sign}{r['chg_pct']:.2f}%</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Math Engine + Gradient Flow ───────────────────────────────────────
        mc1, mc2 = st.columns(2)

        with mc1:
            d1v, d2v, d3v = r["d1"], r["d2"], r["d3"]
            d1c = "deriv-pos" if d1v > 0 else "deriv-neg"
            d2c = "deriv-pos" if d2v > 0 else "deriv-neg"
            d3c = "deriv-pos" if d3v > 0 else "deriv-neg"
            d1s = ("+" if d1v > 0 else "") + f"{d1v:.4f}%"
            d2s = ("↗ +" if d2v > 0 else "↘ ") + f"{abs(d2v):.4f}"
            d3s = ("⚡+" if d3v > 0 else "⚡") + f"{abs(d3v):.2f}"

            st.markdown(f"""
            <div class="detail-card">
              <div class="section-hdr">MATH ENGINE</div>
              <div class="deriv-row">
                <span class="deriv-label">AMA / KAMA</span>
                <span class="deriv-neu">₹{r['ama']:.2f}</span>
              </div>
              <div class="deriv-row">
                <span class="deriv-label">EMA ({ema_len})</span>
                <span class="deriv-neu">₹{r['ema70']:.2f}</span>
              </div>
              <div class="deriv-row">
                <span class="deriv-label">Eff. Ratio</span>
                <span class="deriv-amber">{r['er']:.4f}</span>
              </div>
              <div style="height:6px"></div>
              <div class="deriv-row">
                <span class="deriv-label">f'(x) Velocity</span>
                <span class="{d1c}">{d1s}</span>
              </div>
              <div class="deriv-row">
                <span class="deriv-label">f''(x) Accel</span>
                <span class="{d2c}">{d2s}</span>
              </div>
              <div class="deriv-row">
                <span class="deriv-label">f'''(x) Jerk</span>
                <span class="{d3c}">{d3s}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with mc2:
            if r["gf_bull"]:
                flow_arrow = "↑"
                flow_color = "#00ff41"
                flow_label = "Bullish Flow"
                flow_desc  = "f''(x) > 0  ∧  f'(x) < 0"
            elif r["gf_bear"]:
                flow_arrow = "↓"
                flow_color = "#ff2e2e"
                flow_label = "Bearish Flow"
                flow_desc  = "f''(x) < 0  ∧  f'(x) > 0"
            else:
                flow_arrow = "→"
                flow_color = "#445"
                flow_label = "No Flow"
                flow_desc  = "No gradient reversal"

            str_color = get_bar_color(r["strength"], bull)
            bar_pct   = r["strength"]

            st.markdown(f"""
            <div class="detail-card">
              <div class="section-hdr">GRADIENT FLOW</div>
              <div style="text-align:center;font-size:40px;color:{flow_color};line-height:1.1;margin:4px 0;">
                {flow_arrow}
              </div>
              <div style="text-align:center;color:{flow_color};font-size:10px;font-weight:700;">{flow_label}</div>
              <div style="text-align:center;color:#445;font-size:9px;margin-bottom:8px;">{flow_desc}</div>
              <div class="section-hdr">REVERSAL STRENGTH</div>
              <div style="text-align:center;font-size:24px;font-weight:700;color:{str_color};">
                {r['strength']:.1f}%
              </div>
              <div class="str-bar-bg" style="margin:4px 0 6px;">
                <div class="str-bar" style="width:{bar_pct}%;background:{str_color}"></div>
              </div>
              <div style="text-align:center;">
                <span class="badge {('badge-bull' if bull else ('badge-bear' if bear else 'badge-none'))}"
                      style="font-size:10px;padding:3px 12px;">
                  {rating}
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Components breakdown ───────────────────────────────────────────────
        max_c = max(0.0001, r["c1"] * 0.35, r["c2"] * 0.012, r["c3"] * 0.5)
        c1_pct = min(100, (r["c1"] * 0.35 / max_c) * 100) if r["gf_bull"] or r["gf_bear"] else 0
        c2_pct = min(100, (r["c2"] * 0.012 / max_c) * 100 * 3) if r["gf_bull"] or r["gf_bear"] else 0
        c3_pct = min(100, (r["c3"] * 0.5 / max_c) * 100) if r["gf_bull"] or r["gf_bear"] else 0

        st.markdown(f"""
        <div class="detail-card">
          <div class="section-hdr">STRENGTH COMPONENTS</div>
          <div style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;font-size:9px;color:#556;margin-bottom:2px;">
              <span>C1 — Accel Magnitude (35%)</span><span style="color:#00e5ff;">{r['c1']:.4f}</span>
            </div>
            <div class="str-bar-bg"><div class="str-bar" style="width:{c1_pct:.1f}%;background:#00e5ff;"></div></div>
          </div>
          <div style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;font-size:9px;color:#556;margin-bottom:2px;">
              <span>C2 — Velocity × Accel Divergence (50%)</span><span style="color:#ffc107;">{r['c2']:.4f}</span>
            </div>
            <div class="str-bar-bg"><div class="str-bar" style="width:{c2_pct:.1f}%;background:#ffc107;"></div></div>
          </div>
          <div style="margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;font-size:9px;color:#556;margin-bottom:2px;">
              <span>C3 — Jerk Contribution (15%)</span><span style="color:#ce93d8;">{r['c3']:.4f}</span>
            </div>
            <div class="str-bar-bg"><div class="str-bar" style="width:{c3_pct:.1f}%;background:#ce93d8;"></div></div>
          </div>
          <div style="display:flex;gap:16px;font-size:9px;margin-top:8px;border-top:1px solid #1a1a2e;padding-top:6px;">
            <span style="color:#556;">Raw: <b style="color:#778;">{r['raw_str']:.6f}</b></span>
            <span style="color:#556;">Max: <b style="color:#778;">{r['max_str']:.6f}</b></span>
            <span style="color:#556;">Boost: <b style="color:{'#ffc107' if r['boost'] else '#445'};">{'YES ×1.25' if r['boost'] else 'NO'}</b></span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Rating scale ──────────────────────────────────────────────────────
        st.markdown("""
        <div class="detail-card">
          <div class="section-hdr">SIGNAL RATING SCALE</div>
          <div style="display:flex;gap:3px;margin-bottom:4px;">
            <div style="flex:1;background:#0a1f0a;border:1px solid #1a3a1a;border-radius:3px;padding:4px;text-align:center;">
              <div style="color:#00ff41;font-size:8px;font-weight:700;">80–100%</div>
              <div style="color:#00ff41;font-size:7px;">VERY STRONG</div>
            </div>
            <div style="flex:1;background:#0f1f0f;border:1px solid #1a3a1a;border-radius:3px;padding:4px;text-align:center;">
              <div style="color:#90ee90;font-size:8px;font-weight:700;">60–80%</div>
              <div style="color:#90ee90;font-size:7px;">STRONG</div>
            </div>
            <div style="flex:1;background:#1f1a00;border:1px solid #3a3000;border-radius:3px;padding:4px;text-align:center;">
              <div style="color:#ffc107;font-size:8px;font-weight:700;">40–60%</div>
              <div style="color:#ffc107;font-size:7px;">MODERATE</div>
            </div>
            <div style="flex:1;background:#1f1200;border:1px solid #3a2000;border-radius:3px;padding:4px;text-align:center;">
              <div style="color:#ffa500;font-size:8px;font-weight:700;">20–40%</div>
              <div style="color:#ffa500;font-size:7px;">WEAK</div>
            </div>
            <div style="flex:1;background:#111;border:1px solid #1a1a2e;border-radius:3px;padding:4px;text-align:center;">
              <div style="color:#445;font-size:8px;font-weight:700;">0–20%</div>
              <div style="color:#445;font-size:7px;">VERY WEAK</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Alert History ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-hdr">🔔 ALERT HISTORY</div>', unsafe_allow_html=True)

    if st.session_state.alert_history:
        for a in st.session_state.alert_history[:15]:
            bull_a = a["signal"] == "BULL"
            color_a = "#00ff41" if bull_a else "#ff2e2e"
            arrow_a = "↑" if bull_a else "↓"
            rating_a, _ = get_rating(a["strength"])
            st.markdown(f"""
            <div class="alert-entry {'alert-bull-entry' if bull_a else 'alert-bear-entry'}">
              <div>
                <span style="color:{color_a};font-weight:700;font-size:10px;">{arrow_a} {a['ticker']}</span>
                <span style="color:#556;font-size:9px;margin-left:6px;">{a['name'][:20]}</span><br>
                <span style="color:#445;font-size:9px;">{rating_a}  ◈  ₹{a['price']:,.0f}  ◈  {a['time']}</span>
              </div>
              <span style="color:{color_a};font-size:14px;font-weight:700;">{a['strength']:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="color:#445;font-size:10px;text-align:center;padding:20px;background:#0d0d1a;
             border:1px solid #1a1a2e;border-radius:5px;">
          No alerts yet. Run scan with alert threshold set.
        </div>
        """, unsafe_allow_html=True)


# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
last_scan_str = st.session_state.last_scan.strftime("%H:%M:%S on %d %b %Y") \
                if st.session_state.last_scan else "Not yet scanned"
st.markdown(f"""
<div style="text-align:center;color:#334;font-size:9px;letter-spacing:2px;
     border-top:1px solid #1a1a2e;padding-top:8px;">
  AMA v3.0 GRADIENT BACKPROP ENGINE  ◈  NSE UNIVERSE  ◈  POWERED BY YFINANCE
  &nbsp;|&nbsp; LAST SCAN: {last_scan_str}
  &nbsp;|&nbsp; DATA: EOD VIA YAHOO FINANCE
</div>
""", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(60)
    st.rerun()
