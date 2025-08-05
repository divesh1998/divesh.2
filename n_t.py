import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import os
from PIL import Image

# --- Page Setup ---
st.set_page_config(page_title="Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# --- Create save folder ---
if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# --- Symbol Setup ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "RELIANCE.NS": "RELIANCE.NS",
    "TCS.NS": "TCS.NS",
    "INFY.NS": "INFY.NS"
}

# --- Helper Functions ---

def calculate_rsi(df, period=14):
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def detect_price_action(df):
    patterns = []
    if len(df) < 3:
        return patterns  # Not enough data
    df = df.dropna(subset=["Open", "Close"])  # Drop rows with missing Open/Close

    for i in range(2, len(df)):
        try:
            o1, c1 = df['Open'].iloc[i - 2], df['Close'].iloc[i - 2]
            o2, c2 = df['Open'].iloc[i - 1], df['Close'].iloc[i - 1]

            if pd.isna(o1) or pd.isna(c1) or pd.isna(o2) or pd.isna(c2):
                continue  # Skip if any value is missing

            if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
                patterns.append((df.index[i], 'Bullish Engulfing'))
            elif c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:
                patterns.append((df.index[i], 'Bearish Engulfing'))
        except Exception:
            continue
    return patterns

def detect_elliott_wave_breakout(df):
    if len(df) < 21:
        return False, None
    breakout = df['Close'].iloc[-1] > df['Close'].rolling(window=20).max().iloc[-2]
    return breakout, None

def backtest_strategy_accuracy(df, use_elliott=False, use_price_action=False):
    df = df.copy()
    df['EMA10'] = df['Close'].ewm(span=10).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df = calculate_rsi(df)

    df['Signal'] = 0
    df.loc[(df['EMA10'] > df['EMA20']) & (df['RSI'] > 50), 'Signal'] = 1
    df.loc[(df['EMA10'] < df['EMA20']) & (df['RSI'] < 50), 'Signal'] = -1

    if use_elliott:
        breakout, _ = detect_elliott_wave_breakout(df)
        if not breakout:
            df['Signal'] = 0

    if use_price_action:
        patterns = detect_price_action(df)
        if not patterns:
            df['Signal'] = 0

    df['Return'] = df['Close'].pct_change().shift(-1)
    df['StrategyReturn'] = df['Signal'].shift(1) * df['Return']
    total_signals = df[df['Signal'] != 0]
    correct = df[df['StrategyReturn'] > 0]
    accuracy = round(len(correct) / len(total_signals) * 100, 2) if len(total_signals) else 0
    return accuracy

# --- User Input ---
asset = st.selectbox("Choose Asset", list(symbols.keys()))
timeframe = st.selectbox("Choose Timeframe", ["1h", "15m", "5m"])
sl_buffer = st.slider("SL Buffer (%)", 0.5, 5.0, 1.0)
tp_buffer = st.slider("TP Buffer (%)", 0.5, 10.0, 2.0)

# --- Data Fetch ---
interval_map = {"1h": "60m", "15m": "15m", "5m": "5m"}
df = yf.download(symbols[asset], period="5d", interval=interval_map[timeframe])

if df.empty or len(df) < 21:
    st.warning("Not enough data for analysis.")
    st.stop()

# --- Apply Strategy ---
df = calculate_rsi(df)
df['EMA10'] = df['Close'].ewm(span=10).mean()
df['EMA20'] = df['Close'].ewm(span=20).mean()

patterns = detect_price_action(df)
breakout, _ = detect_elliott_wave_breakout(df)

buy_signal = (df['EMA10'].iloc[-1] > df['EMA20'].iloc[-1]) and (df['RSI'].iloc[-1] > 50) and breakout
sell_signal = (df['EMA10'].iloc[-1] < df['EMA20'].iloc[-1]) and (df['RSI'].iloc[-1] < 50) and breakout

# --- Show Results ---
st.subheader(f"{asset} - {timeframe} Analysis")
if buy_signal:
    st.success("✅ Buy Signal Confirmed")
elif sell_signal:
    st.error("❌ Sell Signal Confirmed")
else:
    st.info("No clear signal at this time.")

st.write(f"RSI: {df['RSI'].iloc[-1]:.2f}")
st.write(f"EMA10: {df['EMA10'].iloc[-1]:.2f}, EMA20: {df['EMA20'].iloc[-1]:.2f}")

# --- Accuracy ---
accuracy = backtest_strategy_accuracy(df, use_elliott=True, use_price_action=True)
st.write(f"Backtested Accuracy: {accuracy}%")
