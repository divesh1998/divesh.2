import yfinance as yf
import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime, timedelta
import os
from PIL import Image

# Page config
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# Save folder
if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# Symbols
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "NIFTY 50": "^NSEI",
    "Bank NIFTY": "^NSEBANK",
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS"
}

# User selection
selected_symbol = st.selectbox("Choose Asset", list(symbols.keys()))
symbol = symbols[selected_symbol]
selected_tf = st.selectbox("Choose Timeframe", ["1h", "15m", "5m"])
interval = {"1h": "60m", "15m": "15m", "5m": "5m"}[selected_tf]
period = {"1h": "7d", "15m": "5d", "5m": "2d"}[selected_tf]

# Load Data
@st.cache_data
def load_data(symbol, period, interval):
    return yf.download(symbol, period=period, interval=interval)

df = load_data(symbol, period, interval)

# Indicators
def apply_indicators(df):
    df['EMA10'] = df['Close'].ewm(span=10).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

df = apply_indicators(df)

# Price Action
def detect_price_action(df):
    patterns = []
    for i in range(2, len(df)):
        o1, c1 = df['Open'].iloc[i-1], df['Close'].iloc[i-1]
        o2, c2 = df['Open'].iloc[i], df['Close'].iloc[i]
        if c2 > o2 and o2 < c1 and c1 < o1:
            patterns.append((df.index[i], "Bullish Engulfing"))
        elif c2 < o2 and o2 > c1 and c1 > o1:
            patterns.append((df.index[i], "Bearish Engulfing"))
        elif df['High'].iloc[i] < df['High'].iloc[i-1] and df['Low'].iloc[i] > df['Low'].iloc[i-1]:
            patterns.append((df.index[i], "Inside Bar"))
    return patterns

# Elliott Wave Breakout
def detect_elliott_wave_breakout(df):
    breakout = False
    reason = ""
    if len(df) > 20:
        recent = df[-20:]
        high_break = recent['Close'].iloc[-1] > recent['Close'].max() * 0.98
        low_break = recent['Close'].iloc[-1] < recent['Close'].min() * 1.02
        if high_break:
            breakout = True
            reason = "Wave 3 Bullish Breakout"
        elif low_break:
            breakout = True
            reason = "Wave 3 Bearish Breakout"
    return breakout, reason

# Signal Logic
def enhanced_signal(df):
    df['Signal'] = 0
    for i in range(1, len(df)):
        if (
            df['EMA10'].iloc[i] > df['EMA20'].iloc[i] and
            df['EMA10'].iloc[i - 1] <= df['EMA20'].iloc[i - 1] and
            df['RSI'].iloc[i] > 50
        ):
            df.at[df.index[i], 'Signal'] = 1
        elif (
            df['EMA10'].iloc[i] < df['EMA20'].iloc[i] and
            df['EMA10'].iloc[i - 1] >= df['EMA20'].iloc[i - 1] and
            df['RSI'].iloc[i] < 50
        ):
            df.at[df.index[i], 'Signal'] = -1
    return df

df = enhanced_signal(df)

# SL/TP
def calculate_sl_tp(entry_price, signal, sl_pct=0.005, tp_pct=0.01):
    if signal == 1:
        return round(entry_price * (1 - sl_pct), 2), round(entry_price * (1 + tp_pct), 2)
    elif signal == -1:
        return round(entry_price * (1 + sl_pct), 2), round(entry_price * (1 - tp_pct), 2)
    return None, None

# Accuracy
def backtest_strategy_accuracy(df, use_elliott=True, use_price_action=True):
    df = df.copy()
    df = enhanced_signal(df)

    if use_elliott:
        breakout, _ = detect_elliott_wave_breakout(df)
        if not breakout:
            df['Signal'] = 0

    if use_price_action:
        patterns = detect_price_action(df)
        if not patterns:
            df['Signal'] = 0

    total_signals = df['Signal'].ne(0).sum()
    wins = 0

    for i in range(len(df) - 1):
        signal = df['Signal'].iloc[i]
        if signal != 0:
            entry = df['Close'].iloc[i]
            sl, tp = calculate_sl_tp(entry, signal)
            next_candle = df['Close'].iloc[i + 1]
            if signal == 1 and next_candle > entry:
                wins += 1
            elif signal == -1 and next_candle < entry:
                wins += 1

    return (wins / total_signals * 100) if total_signals > 0 else 0

# Display
st.subheader(f"📊 {selected_symbol} | Timeframe: {selected_tf}")
st.write(df.tail())

last_signal = df['Signal'].iloc[-1]
current_price = df['Close'].iloc[-1]
sl, tp = calculate_sl_tp(current_price, last_signal)

if last_signal == 1:
    st.success(f"📈 **Buy Signal** at {current_price} | SL: {sl}, TP: {tp}")
elif last_signal == -1:
    st.error(f"📉 **Sell Signal** at {current_price} | SL: {sl}, TP: {tp}")
else:
    st.info("No trade signal at the moment.")

patterns = detect_price_action(df)
if patterns:
    st.markdown("### 🧠 Price Action Patterns Detected")
    for time, pattern in patterns[-5:]:
        st.write(f"{time.strftime('%Y-%m-%d %H:%M')} - {pattern}")

breakout, ew_reason = detect_elliott_wave_breakout(df)
if breakout:
    st.markdown(f"### 🌊 Elliott Wave: **{ew_reason}**")

accuracy = backtest_strategy_accuracy(df, use_elliott=True, use_price_action=True)
st.markdown(f"### 🎯 Strategy Accuracy: **{accuracy:.2f}%**")
