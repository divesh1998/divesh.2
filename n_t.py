import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import datetime
import os

# --- Config ---
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone - Swing & Intraday Trades")

if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# --- Telegram Setup ---
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except:
        pass

# --- Symbols ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS"
}

# --- Helper Functions ---

def calculate_fibonacci(high, low):
    diff = high - low
    levels = {
        '0.0%': high,
        '23.6%': high - 0.236 * diff,
        '38.2%': high - 0.382 * diff,
        '50.0%': high - 0.5 * diff,
        '61.8%': high - 0.618 * diff,
        '100.0%': low
    }
    return levels

def detect_support_resistance(df):
    levels = []
    for i in range(2, len(df) - 2):
        if df['Low'][i] < df['Low'][i-1] and df['Low'][i] < df['Low'][i+1] and \
           df['Low'][i+1] < df['Low'][i+2] and df['Low'][i-1] < df['Low'][i-2]:
            levels.append((i, df['Low'][i]))
        elif df['High'][i] > df['High'][i-1] and df['High'][i] > df['High'][i+1] and \
             df['High'][i+1] > df['High'][i+2] and df['High'][i-1] > df['High'][i-2]:
            levels.append((i, df['High'][i]))
    return levels

def detect_trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        return "Uptrend"
    else:
        return "Downtrend"

def detect_bullish_bearish(df):
    last = df.iloc[-2]
    if last['Close'] > last['Open'] and (last['Close'] - last['Open']) > (last['High'] - last['Low']) * 0.5:
        return "Bullish Candle"
    elif last['Open'] > last['Close'] and (last['Open'] - last['Close']) > (last['High'] - last['Low']) * 0.5:
        return "Bearish Candle"
    else:
        return "No Clear Candle"

def elliott_wave_signal(df):
    # Simplified Elliott Wave detection using pivot highs/lows
    df['PivotHigh'] = df['High'][(df['High'].shift(1) < df['High']) & (df['High'].shift(-1) < df['High'])]
    df['PivotLow'] = df['Low'][(df['Low'].shift(1) > df['Low']) & (df['Low'].shift(-1) > df['Low'])]

    pivot_highs = df['PivotHigh'].dropna()
    pivot_lows = df['PivotLow'].dropna()

    if len(pivot_highs) >= 3 and len(pivot_lows) >= 2:
        wave_1 = pivot_highs.index[-3]
        wave_2 = pivot_lows.index[-2]
        wave_3 = pivot_highs.index[-2]
        wave_4 = pivot_lows.index[-1]
        wave_5 = pivot_highs.index[-1]

        if wave_5 > wave_3 and wave_3 > wave_1:
            return "Wave 5 Completed - Reversal Possible"
        elif wave_3 > wave_1:
            return "Wave 3 Formed - Wait for Pullback"
    return "No Elliott Wave Pattern"

def generate_trade_signal(df, timeframe):
    trend = detect_trend(df)
    candle = detect_bullish_bearish(df)
    ew = elliott_wave_signal(df)

    if trend == "Uptrend" and candle == "Bullish Candle" and "Wave 3" in ew:
        signal = f"BUY ({timeframe})\nTrend: {trend}\nCandle: {candle}\nElliott: {ew}"
    elif trend == "Downtrend" and candle == "Bearish Candle" and "Wave 3" in ew:
        signal = f"SELL ({timeframe})\nTrend: {trend}\nCandle: {candle}\nElliott: {ew}"
    else:
        signal = f"No Trade ({timeframe})\nTrend: {trend}\nCandle: {candle}\nElliott: {ew}"
    return signal

# --- Streamlit UI ---
asset = st.selectbox("Select Asset", options=list(symbols.keys()))
symbol = symbols[asset]

# --- Download Data ---
df_1h = yf.download(symbol, interval='60m', period='7d')
df_15m = yf.download(symbol, interval='15m', period='5d')
df_5m = yf.download(symbol, interval='5m', period='2d')

if len(df_1h) == 0:
    st.warning("Data load failed. Try again.")
    st.stop()

# --- Analysis ---
st.subheader("🔍 1H Analysis (Swing Trade)")
signal_1h = generate_trade_signal(df_1h, "1H")
st.text(signal_1h)

st.subheader("📊 15M Analysis (Intraday Trade)")
signal_15m = generate_trade_signal(df_15m, "15M")
st.text(signal_15m)

st.subheader("⚡ 5M Entry Confirmation")
signal_5m = generate_trade_signal(df_5m, "5M")
st.text(signal_5m)

# --- Telegram Alert Button ---
if st.button("📩 Send Signal to Telegram"):
    message = f"""
🛎️ Divesh Market Zone Signal 🛎️

📈 {asset}
🕐 1H: {signal_1h}
⏱️ 15M: {signal_15m}
⚡ 5M: {signal_5m}
"""
    send_telegram_alert(message)
    st.success("Signal sent to Telegram ✅")
