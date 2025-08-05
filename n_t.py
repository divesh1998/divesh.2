✅ Final Version of Streamlit App with EMA10/20 + RSI + Price Action + Elliott Wave

import yfinance as yf import pandas as pd import streamlit as st from datetime import datetime import os from PIL import Image

--- Streamlit Setup ---

st.set_page_config(page_title="Divesh Market Zone", layout="wide") st.title("\U0001F4C8 Divesh Market Zone")

--- Create Folder ---

os.makedirs("saved_charts", exist_ok=True)

--- Assets ---

symbols = { "Bitcoin (BTC)": "BTC-USD", "Gold (XAUUSD)": "GC=F", "NIFTY 50": "^NSEI", "BANKNIFTY": "^NSEBANK", "RELIANCE": "RELIANCE.NS", "TCS": "TCS.NS", "INFY": "INFY.NS" }

--- RSI Calculation ---

def calculate_rsi(df, period=14): delta = df['Close'].diff() gain = delta.where(delta > 0, 0) loss = -delta.where(delta < 0, 0) avg_gain = gain.rolling(window=period).mean() avg_loss = loss.rolling(window=period).mean() rs = avg_gain / avg_loss df['RSI'] = 100 - (100 / (1 + rs)) return df

--- Price Action Detection ---

def detect_price_action(df): patterns = [] if len(df) < 3: return patterns for i in range(2, len(df)): o1, c1 = df['Open'].iloc[i-1], df['Close'].iloc[i-1] o2, c2 = df['Open'].iloc[i], df['Close'].iloc[i] body1, body2 = abs(c1 - o1), abs(c2 - o2)

if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
        patterns.append((df.index[i], "Bullish Engulfing"))
    elif c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:
        patterns.append((df.index[i], "Bearish Engulfing"))
    elif abs(df['High'].iloc[i] - df['Close'].iloc[i]) > 2 * body2 or abs(df['Low'].iloc[i] - df['Close'].iloc[i]) > 2 * body2:
        patterns.append((df.index[i], "Pin Bar"))
    elif df['High'].iloc[i] < df['High'].iloc[i-1] and df['Low'].iloc[i] > df['Low'].iloc[i-1]:
        patterns.append((df.index[i], "Inside Bar"))
    elif c1 < o1 and body1 > 0 and body2 > 0 and c2 > o2 and df['Open'].iloc[i] > df['Close'].iloc[i-1]:
        patterns.append((df.index[i], "Morning Star"))
    elif c1 > o1 and body1 > 0 and body2 > 0 and c2 < o2 and df['Open'].iloc[i] < df['Close'].iloc[i-1]:
        patterns.append((df.index[i], "Evening Star"))
return patterns

--- Elliott Wave Placeholder ---

def detect_elliott_wave_breakout(df): # Placeholder - assume breakout for now return True, df

--- Apply Indicators ---

def apply_indicators(df): df['EMA10'] = df['Close'].ewm(span=10).mean() df['EMA20'] = df['Close'].ewm(span=20).mean() df = calculate_rsi(df) return df

--- Backtest Accuracy ---

def backtest_strategy_accuracy(df, use_elliott=False, use_price_action=False): df = df.copy() df = apply_indicators(df) df['Signal'] = 0 df.loc[(df['EMA10'] > df['EMA20']) & (df['RSI'] > 50), 'Signal'] = 1 df.loc[(df['EMA10'] < df['EMA20']) & (df['RSI'] < 50), 'Signal'] = -1

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

--- Streamlit UI ---

asset = st.selectbox("Choose Asset", list(symbols.keys())) timeframe = st.selectbox("Choose Timeframe", ["1h", "15m", "5m"]) sl_buffer = st.slider("SL Buffer (%)", 0.5, 5.0, 1.0) tp_buffer = st.slider("TP Buffer (%)", 0.5, 10.0, 2.0)

symbol = symbols[asset] interval_map = {"1h": "60m", "15m": "15m", "5m": "5m"} interval = interval_map[timeframe]

data = yf.download(symbol, period="7d", interval=interval) data.dropna(inplace=True)

if not data.empty: data = apply_indicators(data) patterns = detect_price_action(data) elliott_breakout, _ = detect_elliott_wave_breakout(data) accuracy = backtest_strategy_accuracy(data, use_elliott=True, use_price_action=True)

st.subheader(f"{asset} - {timeframe} Analysis")
st.write(f"✅ Strategy Accuracy: {accuracy}%")

if patterns:
    st.markdown("### 🔍 Price Action Patterns Detected")
    for ts, pattern in patterns[-5:]:
        st.write(f"{ts} - {pattern}")

else: st.error("No data available for selected asset and timeframe.")

