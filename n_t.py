import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# --- Asset selection ---
assets = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK"
}

selected_asset = st.selectbox("📌 Select Asset", list(assets.keys()))
symbol = assets[selected_asset]

# --- Timeframe selection ---
timeframes = {
    "1D": "1d",
    "4H": "60m",
    "1H": "60m",
    "15M": "15m",
    "5M": "5m"
}
selected_tf = st.selectbox("🕒 Select Timeframe", list(timeframes.keys()))
interval = timeframes[selected_tf]

# --- Fetch Data ---
def get_data(symbol, interval, period="30d"):
    df = yf.download(symbol, interval=interval, period=period)
    df.dropna(inplace=True)
    return df

df = get_data(symbol, interval)

# --- Indicators ---
df['EMA20'] = EMAIndicator(df['Close'], window=20).ema_indicator()
df['EMA50'] = EMAIndicator(df['Close'], window=50).ema_indicator()
df['RSI'] = RSIIndicator(df['Close'], window=14).rsi()

# --- Trend Detection ---
def detect_trend(row):
    if row['EMA20'] > row['EMA50']:
        return "Uptrend"
    elif row['EMA20'] < row['EMA50']:
        return "Downtrend"
    else:
        return "Sideways"

df['Trend'] = df.apply(detect_trend, axis=1)

# --- Signal Detection (Scalping) ---
def scalping_signal(row):
    if row['Trend'] == "Uptrend" and row['RSI'] < 70:
        return "Buy"
    elif row['Trend'] == "Downtrend" and row['RSI'] > 30:
        return "Sell"
    else:
        return None

df['Signal'] = df.apply(scalping_signal, axis=1)

# --- Show latest signal ---
latest_signal = df['Signal'].iloc[-1]
latest_trend = df['Trend'].iloc[-1]
current_price = df['Close'].iloc[-1]

st.subheader(f"📊 {selected_asset} - {selected_tf} Analysis")
st.write(f"**Current Price:** {current_price:.2f}")
st.write(f"**Trend:** {latest_trend}")
st.write(f"**Signal:** {latest_signal or 'No Signal'}")

# --- Chart Plot ---
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    name='Candles'
))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], line=dict(color='blue', width=1), name='EMA20'))
fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], line=dict(color='red', width=1), name='EMA50'))

st.plotly_chart(fig, use_container_width=True)
