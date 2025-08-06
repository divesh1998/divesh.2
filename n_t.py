import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import requests
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
import plotly.graph_objects as go

# --- Telegram Config ---
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

# --- App Setup ---
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📊 Divesh Market Zone - Swing & Intraday Analysis")

# --- Asset Selection ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Reliance (Futures)": "RELIANCE.BO",
    "TCS (Futures)": "TCS.BO"
}
symbol_name = st.selectbox("📌 Choose Asset", list(symbols.keys()))
ticker = symbols[symbol_name]

# --- Timeframe ---
timeframe = st.selectbox("⏱️ Select Timeframe", ["1d", "4h", "1h", "15m", "5m"])
period_map = {"1d": "6mo", "4h": "60d", "1h": "30d", "15m": "7d", "5m": "5d"}
interval_map = {"1d": "1d", "4h": "1h", "1h": "1h", "15m": "15m", "5m": "5m"}

# --- Fetch Data ---
@st.cache_data
def load_data(ticker, period, interval):
    df = yf.download(ticker, period=period, interval=interval)
    df.dropna(inplace=True)
    return df

df = load_data(ticker, period_map[timeframe], interval_map[timeframe])

# --- Fibonacci & Elliott Wave (Simplified Logic) ---
def apply_elliott_wave(df):
    wave_signals = []
    fib_levels = []
    for i in range(5, len(df)):
        recent = df.iloc[i-5:i]
        low = recent['Low'].min()
        high = recent['High'].max()
        retracement = (high - low) * 0.618
        level = high - retracement
        close = df.iloc[i]['Close']
        if close > high:
            wave_signals.append((df.index[i], "Wave 3 Breakout (Buy)", close))
            fib_levels.append((df.index[i], high, level))
        elif close < low:
            wave_signals.append((df.index[i], "Wave 3 Breakdown (Sell)", close))
            fib_levels.append((df.index[i], low, low + retracement))
    return wave_signals, fib_levels

wave_signals, fib_levels = apply_elliott_wave(df)

# --- Plotting ---
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Candles'))

# Plot Fibonacci
for time, high, level in fib_levels[-5:]:
    fig.add_hline(y=level, line=dict(color='blue', dash='dot'), annotation_text="Fibo 0.618", annotation_position="top right")

# Plot Signals
for time, signal, price in wave_signals[-5:]:
    fig.add_trace(go.Scatter(x=[time], y=[price],
        mode='markers+text',
        marker=dict(color='green' if "Buy" in signal else 'red', size=10),
        text=[signal],
        textposition="top center"))

st.plotly_chart(fig, use_container_width=True)

# --- Alerts Display ---
if wave_signals:
    st.subheader("📢 Trade Signals")
    for time, signal, price in wave_signals[-3:]:
        st.markdown(f"**🕒 {time.strftime('%Y-%m-%d %H:%M')}** — {signal} at `{round(price, 2)}`")
        send_telegram_alert(f"{symbol_name} {signal} at {round(price, 2)}")

# --- Strategy Summary ---
st.sidebar.markdown("### Strategy Summary")
st.sidebar.markdown("""
- ✅ **Fibonacci 0.618** retracement with breakout logic  
- ✅ **Wave 3 Confirmation** = Entry trigger  
- ✅ Futures & Spot Support  
- ✅ Real-Time Telegram Alert  
""")
