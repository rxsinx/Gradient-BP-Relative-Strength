Gradient Backprop + Reversal Strength | NSE Scanner

## Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

- **~150 NSE equities** scanned across Nifty 50, Nifty Next 50, and Midcap
- **Full KAMA engine** with ER-based adaptive smoothing constant
- **3-order derivative calculus**: f'(x) velocity, f''(x) acceleration, f'''(x) jerk
- **Gradient backprop flow detection**: bullish (f''>0 ∧ f'<0) and bearish (f''<0 ∧ f'>0)
- **Reversal strength 0–100%** with 3 components + normalization + boost
- **Per-minute alert system** for signals above configurable threshold
- **Full dark terminal UI** with JetBrains Mono

## Parameters (all configurable in sidebar)

| Parameter | Default | Description |
|-----------|---------|-------------|
| ER Window | 10 | Efficiency Ratio lookback |
| Fast SC Period | 6 | Fast smoothing constant |
| Slow SC Period | 7 | Slow smoothing constant |
| Derivative Order | 3 | 1=velocity, 2=+accel, 3=+jerk |
| Strength Lookback | 20 | Rolling window for normalization |
| Min Signal Strength | 50% | Filter threshold |
| Alert Threshold | 80% | Notification threshold |

## Data Source

Yahoo Finance via `yfinance`. All tickers use `.NS` suffix for NSE.
Data is cached for 60 seconds. EOD data on `1d` interval; `1wk` available.

## Upgrade to Live Data

Replace `fetch_ohlc()` with Zerodha Kite WebSocket or Upstox API for intraday 
1-minute bars and true per-minute signal updates.
