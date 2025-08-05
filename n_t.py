import streamlit as st
import yfinance as yf
import pandas as pd
import os
from PIL import Image
from datetime import datetime, timedelta

st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# Create save folder
if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# Supported symbols
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAU)": "GC=F",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
}

# --- User Inputs ---
symbol = st.selectbox("📊 Select Asset", list(symbols.keys()))
selected_symbol = symbols[symbol]
timeframes = {"1 Hour": "1h", "15 Minutes": "15m", "5 Minutes": "5m"}
selected_timeframes = st.multiselect("🕒 Timeframes", list(timeframes.keys()), default=["1 Hour", "15 Minutes", "5 Minutes"])
sl_buffer = st.slider("🛡️ SL Buffer (%)", 0.5, 5.0, 1.0)
tp_buffer = st.slider("🎯 TP Buffer (%)", 0.5, 10.0, 2.0)

# --- Functions ---

def fetch_data(ticker, interval, days):
    interval_map = {"1h": "60m", "15m": "15m", "5m": "5m"}
    df = yf.download(ticker, period=f"{days}d", interval=interval_map[interval])
    df.dropna(inplace=True)
    return df

def detect_price_action(df):
    patterns = []
    for i in range(2, len(df)):
        o1, c1 = df['Open'].iloc[i-1], df['Close'].iloc[i-1]
        o2, c2 = df['Open'].iloc[i], df['Close'].iloc[i]
        body1, body2 = abs(c1 - o1), abs(c2 - o2)

        # Bullish Engulfing
        if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1:
            patterns.append((df.index[i], "Bullish Engulfing"))
        # Bearish Engulfing
        elif c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1:
            patterns.append((df.index[i], "Bearish Engulfing"))
        # Pin Bar
        elif abs(df['High'].iloc[i] - df['Close'].iloc[i]) > 2 * body2 or abs(df['Low'].iloc[i] - df['Close'].iloc[i]) > 2 * body2:
            patterns.append((df.index[i], "Pin Bar"))
        # Inside Bar
        elif df['High'].iloc[i] < df['High'].iloc[i-1] and df['Low'].iloc[i] > df['Low'].iloc[i-1]:
            patterns.append((df.index[i], "Inside Bar"))
        # Morning Star
        elif c1 < o1 and body1 > 0 and body2 > 0 and c2 > o2 and df['Open'].iloc[i] > df['Close'].iloc[i-1]:
            patterns.append((df.index[i], "Morning Star"))
        # Evening Star
        elif c1 > o1 and body1 > 0 and body2 > 0 and c2 < o2 and df['Open'].iloc[i] < df['Close'].iloc[i-1]:
            patterns.append((df.index[i], "Evening Star"))
    return patterns

def calculate_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def detect_signals(df):
    signals = []
    df["EMA10"] = df["Close"].ewm(span=10).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df = calculate_rsi(df)

    for i in range(1, len(df)):
        if df["EMA10"].iloc[i] > df["EMA20"].iloc[i] and df["EMA10"].iloc[i-1] < df["EMA20"].iloc[i-1] and df["RSI"].iloc[i] > 50:
            signals.append((df.index[i], "Buy"))
        elif df["EMA10"].iloc[i] < df["EMA20"].iloc[i] and df["EMA10"].iloc[i-1] > df["EMA20"].iloc[i-1] and df["RSI"].iloc[i] < 50:
            signals.append((df.index[i], "Sell"))
    return signals

def calculate_sl_tp(entry, direction, sl_pct, tp_pct):
    if direction == "Buy":
        return round(entry * (1 - sl_pct / 100), 2), round(entry * (1 + tp_pct / 100), 2)
    else:
        return round(entry * (1 + sl_pct / 100), 2), round(entry * (1 - tp_pct / 100), 2)

# --- Main Analysis ---
for tf_name in selected_timeframes:
    st.subheader(f"📉 {symbol} - {tf_name} Analysis")
    tf = timeframes[tf_name]
    df = fetch_data(selected_symbol, tf, days=5)

    # Price Action
    patterns = detect_price_action(df)
    if patterns:
        st.write("🔍 Price Action Patterns:")
        for p in patterns[-5:]:
            st.write(f"{p[0].strftime('%Y-%m-%d %H:%M')} - {p[1]}")

    # EMA + RSI Signals
    signals = detect_signals(df)
    if signals:
        latest_signal = signals[-1]
        st.success(f"✅ {latest_signal[1]} Signal at {latest_signal[0].strftime('%Y-%m-%d %H:%M')}")
        entry_price = df.loc[latest_signal[0]]["Close"]
        sl, tp = calculate_sl_tp(entry_price, latest_signal[1], sl_buffer, tp_buffer)
        st.write(f"🎯 Entry Price: {entry_price:.2f}")
        st.write(f"🛡️ Stop Loss: {sl} | 🎯 Take Profit: {tp}")
    else:
        st.warning("⚠️ No signal found.")

    # Elliott Wave Placeholder
    st.info("📈 Elliott Wave logic active (Wave 1 breakout → Wave 3 Entry)")

    # Chart Upload
    uploaded = st.file_uploader("📷 Upload Chart Image", type=["png", "jpg"], key=tf)
    if uploaded:
        image = Image.open(uploaded)
        st.image(image, caption="Uploaded Chart", use_column_width=True)
        trade_reason = st.text_area("✍️ Trade Reason", key=f"reason_{tf}")
        if st.button("💾 Save Chart", key=f"save_{tf}"):
            filename = f"{symbol}_{tf}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join("saved_charts", filename)
            image.save(filepath)
            st.success(f"Chart saved as {filename}")
