import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import datetime as dt

# --- App Setup ---
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone - Swing + Intraday + Futures Analysis")

# --- Symbol Input ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS"
}
symbol = st.selectbox("📌 Select Asset", list(symbols.keys()))
ticker = symbols[symbol]

# --- Telegram Setup ---
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

# --- Load Data ---
@st.cache_data(ttl=3600)
def load_data(ticker, interval, period):
    df = yf.download(ticker, interval=interval, period=period)
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

# --- EMA Trend ---
def ema_trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    trend = "Uptrend" if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1] else "Downtrend"
    return trend

# --- Fibonacci Support ---
def fibonacci_levels(df):
    max_price = df['High'].max()
    min_price = df['Low'].min()
    diff = max_price - min_price
    levels = {
        "0.0%": max_price,
        "23.6%": max_price - 0.236 * diff,
        "38.2%": max_price - 0.382 * diff,
        "50.0%": max_price - 0.5 * diff,
        "61.8%": max_price - 0.618 * diff,
        "78.6%": max_price - 0.786 * diff,
        "100.0%": min_price
    }
    return levels

# --- Elliott Wave Detection (Basic) ---
def elliott_wave(df):
    wave = None
    if df['High'].iloc[-1] > df['High'].iloc[-2] and df['Low'].iloc[-1] > df['Low'].iloc[-2]:
        wave = "Wave 3 - Breakout Possible"
    elif df['Low'].iloc[-1] < df['Low'].iloc[-2] and df['High'].iloc[-1] < df['High'].iloc[-2]:
        wave = "Wave C - Downside Correction"
    return wave

# --- Price Action ---
def price_action(df):
    signals = []
    for i in range(2, len(df)):
        open_, close = df['Open'][i], df['Close'][i]
        prev_open, prev_close = df['Open'][i-1], df['Close'][i-1]

        # Bullish Engulfing
        if close > open_ and prev_close < prev_open and close > prev_open and open_ < prev_close:
            signals.append((df['Datetime'][i], 'Bullish Engulfing'))
        # Bearish Engulfing
        elif close < open_ and prev_close > prev_open and close < prev_open and open_ > prev_close:
            signals.append((df['Datetime'][i], 'Bearish Engulfing'))
    return signals

# --- Trendline Breakout (simplified) ---
def trendline_breakout(df):
    recent_high = df['High'][-5:].max()
    recent_low = df['Low'][-5:].min()
    last_close = df['Close'].iloc[-1]

    if last_close > recent_high:
        return "Resistance Breakout"
    elif last_close < recent_low:
        return "Support Breakdown"
    return "No Breakout"

# --- Timeframe Analysis ---
timeframes = {
    "1D": ("1d", "3mo"),
    "4H": ("1h", "60d"),
    "1H": ("1h", "15d"),
    "15M": ("15m", "7d"),
    "5M": ("5m", "5d")
}

for label, (interval, period) in timeframes.items():
    st.subheader(f"📊 {label} Analysis")
    df = load_data(ticker, interval, period)
    df.rename(columns={"Datetime": "Datetime"}, inplace=True)
    trend = ema_trend(df)
    fibo = fibonacci_levels(df)
    wave = elliott_wave(df)
    pa = price_action(df)
    breakout = trendline_breakout(df)

    st.write(f"🔹 Trend: **{trend}**")
    st.write(f"🔹 Elliott Wave Signal: **{wave or 'Neutral'}**")
    st.write(f"🔹 Trendline Breakout: **{breakout}**")

    if pa:
        st.markdown("🔍 **Price Action Patterns:**")
        for ts, pat in pa[-3:]:
            st.write(f"{ts} - {pat}")

    with st.expander(f"📉 Fibonacci Levels ({label})"):
        for level, price in fibo.items():
            st.write(f"{level}: {round(price, 2)}")

    # Send alert for 15M or 5M signals
    if label in ["15M", "5M"]:
        if wave or breakout != "No Breakout":
            message = f"⚠️ {label} ALERT for {symbol}\nTrend: {trend}\nWave: {wave}\nBreakout: {breakout}"
            send_telegram(message)

# --- Note ---
st.info("This app provides swing and intraday signals using Elliott Wave + Fibonacci + Price Action + Trendline logic. Use proper risk management.")
