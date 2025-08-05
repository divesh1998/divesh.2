import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import os
from PIL import Image

st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# --- Create save folder ---
if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# --- Symbols ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAU)": "GC=F"
}
symbol = st.selectbox("Select Asset", list(symbols.keys()))
symbol_yf = symbols[symbol]
timeframes = {"1H": "1h", "15M": "15m", "5M": "5m"}

# --- Data Fetch ---
def get_data(symbol, interval, period='7d'):
    df = yf.download(symbol, interval=interval, period=period)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df

# --- Trend Detection ---
def detect_trend(df):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    ema_diff = df['EMA20'] - df['EMA50']
    if ema_diff.iloc[-1] > 0 and ema_diff.iloc[-2] > 0 and ema_diff.iloc[-3] > 0:
        return "Uptrend"
    elif ema_diff.iloc[-1] < 0 and ema_diff.iloc[-2] < 0 and ema_diff.iloc[-3] < 0:
        return "Downtrend"
    else:
        return "Sideways"

# --- Scalping Signal with EMA10/20 ---
def generate_scalping_signals(df):
    df['EMA10'] = df['Close'].ewm(span=10).mean()
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['Signal'] = 0
    for i in range(1, len(df)):
        if df['EMA10'].iloc[i] > df['EMA20'].iloc[i] and df['EMA10'].iloc[i-1] <= df['EMA20'].iloc[i-1]:
            df.at[df.index[i], 'Signal'] = 1
        elif df['EMA10'].iloc[i] < df['EMA20'].iloc[i] and df['EMA10'].iloc[i-1] >= df['EMA20'].iloc[i-1]:
            df.at[df.index[i], 'Signal'] = -1
    return df

# --- SL/TP ---
def generate_sl_tp(price, signal, trend):
    atr = 0.015 if trend == "Uptrend" else 0.02
    rr = 2.0
    if signal == 1:
        sl = price * (1 - atr)
        tp = price + (price - sl) * rr
    elif signal == -1:
        sl = price * (1 + atr)
        tp = price - (sl - price) * rr
    else:
        sl = tp = price
    return round(sl, 2), round(tp, 2)

# --- Accuracy ---
def backtest_scalping_accuracy(df):
    df = generate_scalping_signals(df)
    df['Return'] = df['Close'].pct_change().shift(-1)
    df['StrategyReturn'] = df['Signal'].shift(1) * df['Return']
    total_signals = df[df['Signal'] != 0]
    correct = df[df['StrategyReturn'] > 0]
    accuracy = round(len(correct) / len(total_signals) * 100, 2) if len(total_signals) else 0
    return accuracy

# --- Upload Chart ---
uploaded_image = st.file_uploader("📸 Upload Chart", type=["png", "jpg", "jpeg"])
trade_reason = st.text_area("📜 Enter Trade Reason")
if st.button("💾 Save Chart & Reason"):
    if uploaded_image is not None:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_image.name}"
        filepath = os.path.join("saved_charts", filename)
        with open(filepath, "wb") as f:
            f.write(uploaded_image.read())
        with open(filepath + ".txt", "w", encoding="utf-8") as f:
            f.write(trade_reason)
        st.success("✅ Chart and Reason Saved!")

# --- Show Saved Charts ---
st.subheader("📁 Saved Charts")
for file in os.listdir("saved_charts"):
    if file.lower().endswith((".png", ".jpg", ".jpeg")):
        st.image(os.path.join("saved_charts", file), width=350)
        txt_file = os.path.join("saved_charts", file + ".txt")
        if os.path.exists(txt_file):
            with open(txt_file, "r", encoding="utf-8") as f:
                reason = f.read()
            st.caption(f"📜 Reason: {reason}")

# --- Multi-Timeframe Analysis ---
for tf_label, tf_code in timeframes.items():
    st.markdown("---")
    st.subheader(f"🕒 Timeframe: {tf_label}")

    df = get_data(symbol_yf, tf_code)
    trend = detect_trend(df)
    df = generate_scalping_signals(df)

    if tf_label in ["15M", "5M"] and trend == "Sideways":
        signal = 0
    elif not df[df["Signal"] != 0].empty:
        signal_index = df[df["Signal"] != 0].index[-1]
        signal = df.loc[signal_index, "Signal"]
        price = round(df.loc[signal_index, "Close"], 2)
    else:
        signal_index = df.index[-1]
        signal = 0
        price = round(df["Close"].iloc[-1], 2)

    sl, tp = generate_sl_tp(price, signal, trend)
    reward = abs(tp - price)
    risk = abs(price - sl)
    rr_ratio = round(reward / risk, 2) if risk != 0 else "∞"
    signal_text = "🟢 Buy" if signal == 1 else "🔴 Sell" if signal == -1 else "⚪ No Signal"
    accuracy = backtest_scalping_accuracy(df)

    st.write(f"**Trend:** `{trend}`")
    st.write(f"**Signal:** `{signal_text}`")
    st.metric("🎯 Scalping Strategy Accuracy", f"{accuracy}%")
    st.write(f"**Entry Price:** `{price}` | **SL:** `{sl}` | **TP:** `{tp}`")
    st.write(f"📊 **Risk/Reward Ratio:** `{rr_ratio}`")

    # --- Scalping Badge ---
    if tf_label in ["15M", "5M"]:
        if trend == "Sideways":
            scalping_label = '<span style="color:orange; font-weight:bold;">⚠️ Scalping Zone (Sideways Market)</span>'
        else:
            scalping_label = '<span style="color:green; font-weight:bold;">✅ Trend Zone (Scalping Allowed)</span>'
    else:
        scalping_label = '<span style="color:gray;">🔍 Higher Timeframe (Scalping Not Applicable)</span>'

    st.markdown(f"**Scalping Status:** {scalping_label}", unsafe_allow_html=True)
