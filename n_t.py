# Divesh Market Zone - Final Full Code
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from PIL import Image
import os

# --- App Setup ---
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone - Swing & Intraday Trades")

# --- Telegram Setup ---
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=payload)
    except:
        st.warning("⚠️ Telegram alert failed")

# --- Symbols ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "Nifty 50": "^NSEI",
    "Bank Nifty": "^NSEBANK",
    "Reliance": "RELIANCE.NS",
    "Infosys": "INFY.NS",
}

# --- User Input ---
selected_symbol = st.selectbox("Select Asset", list(symbols.keys()))
symbol = symbols[selected_symbol]
timeframes = {"1D": "1d", "4H": "1h", "1H": "1h", "15M": "15m", "5M": "5m"}
selected_tf = st.selectbox("Select Timeframe", list(timeframes.keys()))
interval = timeframes[selected_tf]
df = yf.download(symbol, interval=interval, period="7d")
df.dropna(inplace=True)

# --- EMA, RSI ---
df['EMA10'] = df['Close'].ewm(span=10).mean()
df['EMA20'] = df['Close'].ewm(span=20).mean()
df['EMA50'] = df['Close'].ewm(span=50).mean()
df['RSI'] = 100 - (100 / (1 + df['Close'].pct_change().rolling(14).mean() / df['Close'].pct_change().rolling(14).std()))

# --- Fibonacci for Elliott Wave ---
def fib_levels(start, end):
    diff = end - start
    return {
        "0.0": start,
        "0.382": start + 0.382 * diff,
        "0.5": start + 0.5 * diff,
        "0.618": start + 0.618 * diff,
        "1.0": end
    }

# --- Trend Detection ---
def detect_trend(df):
    if df['EMA20'].iloc[-1] > df['EMA50'].iloc[-1]:
        return "Uptrend"
    elif df['EMA20'].iloc[-1] < df['EMA50'].iloc[-1]:
        return "Downtrend"
    else:
        return "Sideways"

trend = detect_trend(df)

# --- Price Action Swing Logic (1H Only) ---
def price_action_signal(df):
    candle = df.iloc[-1]
    prev = df.iloc[-2]
    if selected_tf == "1H":
        if candle['Close'] > candle['Open'] and candle['Low'] <= prev['Low']:
            return "Swing Buy", candle['Close'], candle['Low'], candle['Close'] + (candle['Close'] - candle['Low']) * 2
        elif candle['Close'] < candle['Open'] and candle['High'] >= prev['High']:
            return "Swing Sell", candle['Close'], candle['High'], candle['Close'] - (candle['High'] - candle['Close']) * 2
    return None, None, None, None

# --- Elliott Wave Detection (15M + 5M) ---
def elliott_wave_signal(df):
    waves = []
    for i in range(5, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1] > df['Close'].iloc[i-2]:
            waves.append(('Wave 1', df['Close'].iloc[i-2]))
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1] < df['Close'].iloc[i-2]:
            waves.append(('Wave 2', df['Close'].iloc[i-2]))
    if len(waves) >= 2:
        start = waves[0][1]
        end = waves[-1][1]
        fibs = fib_levels(start, end)
        return "Wave Breakout", end, fibs['0.382'], fibs['1.0']
    return None, None, None, None

# --- Signal Generation ---
signal = None
entry = sl = tp = None
trade_type = ""

if selected_tf in ["1H"]:
    signal, entry, sl, tp = price_action_signal(df)
    trade_type = "Swing"
elif selected_tf in ["15M", "5M"]:
    signal, entry, sl, tp = elliott_wave_signal(df)
    trade_type = "Intraday" if selected_tf == "15M" else "Scalping"

# --- Display Output ---
st.subheader("📊 Analysis Summary")
st.write(f"🕒 Timeframe: {selected_tf}")
st.write(f"📈 Trend: {trend}")

if signal:
    st.success(f"📍 Signal: {signal} | 💼 Type: {trade_type}")
    st.write(f"🔹 Entry: {entry:.2f}")
    st.write(f"🔸 SL: {sl:.2f}")
    st.write(f"🟢 TP: {tp:.2f}")
    
    # --- Telegram Alert ---
    msg = f"""
🔔 *Trade Alert - {selected_symbol}*
📉 Timeframe: {selected_tf}
📈 Trend: {trend}
📍 Signal: {signal}
💼 Type: {trade_type}
🔹 Entry: {entry:.2f}
🔸 SL: {sl:.2f}
🟢 TP: {tp:.2f}
    """
    send_telegram_alert(msg)

else:
    st.warning("🚫 No valid trade setup found right now.")
