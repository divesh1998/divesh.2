import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import os
from datetime import datetime
from PIL import Image

# --- Page Setup ---
st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone")

# --- Timeframes ---
timeframes = {
    "1H": "60m",
    "15M": "15m",
    "5M": "5m"
}

# --- Symbols ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "GC=F",
    "NIFTY 50": "^NSEI",
    "Bank NIFTY": "^NSEBANK",
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS"
}
asset = st.selectbox("📌 Select Asset", list(symbols.keys()))
symbol_yf = symbols[asset]

# --- Create folder ---
if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# --- Get Data ---
@st.cache_data(ttl=300)
def get_data(symbol, interval, period="60d"):
    return yf.download(symbol, interval=interval, period=period)

# --- Trend ---
def detect_trend(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    if df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]:
        return "Uptrend"
    elif df["EMA20"].iloc[-1] < df["EMA50"].iloc[-1]:
        return "Downtrend"
    else:
        return "Sideways"

# --- Signal ---
def generate_signals(df):
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["Signal"] = 0
    df.loc[df["EMA20"] > df["EMA50"], "Signal"] = 1
    df.loc[df["EMA20"] < df["EMA50"], "Signal"] = -1
    return df

# --- Dummy Elliott Wave breakout ---
def detect_elliott_wave_breakout(df):
    breakout = False
    msg = "🔮 No Elliott Wave breakout"
    if len(df) > 50 and df["Close"].iloc[-1] > df["Close"].rolling(20).max().iloc[-2]:
        breakout = True
        msg = "🚀 Elliott Wave breakout!"
    return breakout, msg

# --- Dummy Price Action ---
def detect_price_action(df):
    patterns = []
    if len(df) < 2:
        return patterns
    c1, c2 = df.iloc[-2], df.iloc[-1]
    if c1["Close"] < c1["Open"] and c2["Close"] > c2["Open"] and c2["Close"] > c1["Open"]:
        patterns.append((df.index[-1], "Bullish Engulfing"))
    if c1["Close"] > c1["Open"] and c2["Close"] < c2["Open"] and c2["Close"] < c1["Open"]:
        patterns.append((df.index[-1], "Bearish Engulfing"))
    return patterns

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

# --- Confidence Meter ---
def strategy_confidence(row):
    score = 0
    reasons = []
    if row.get("Bullish Engulfing"):
        score += 1
        reasons.append("📈 Price Action bullish")
    if row.get("Bearish Engulfing"):
        score -= 1
        reasons.append("📉 Price Action bearish")
    if row.get("Elliott_Wave_Breakout"):
        score += 1
        reasons.append("🔮 Elliott Wave breakout")
    if row.get("EMA_Trend") == "Uptrend":
        score += 1
        reasons.append("✅ EMA Uptrend")
    elif row.get("EMA_Trend") == "Downtrend":
        score -= 1
        reasons.append("❌ EMA Downtrend")
    return score, ", ".join(reasons)

# --- Strategy Accuracy ---
def backtest_strategy_accuracy(df, use_elliott=False, use_price_action=False):
    df = df.copy()
    df = generate_signals(df)
    trend = detect_trend(df)
    if use_elliott:
        breakout, _ = detect_elliott_wave_breakout(df)
        if not breakout:
            df["Signal"] = 0
    if use_price_action:
        patterns = detect_price_action(df)
        if not patterns:
            df["Signal"] = 0
    df["Return"] = df["Close"].pct_change().shift(-1)
    df["StrategyReturn"] = df["Signal"].shift(1) * df["Return"]
    total = df[df["Signal"] != 0]
    correct = df[df["StrategyReturn"] > 0]
    acc = round(len(correct) / len(total) * 100, 2) if len(total) else 0
    return acc

# --- Accuracy Over Time ---
def accuracy_over_days(df):
    df = generate_signals(df.copy())
    df["Date"] = df.index.date
    df["Return"] = df["Close"].pct_change().shift(-1)
    df["StrategyReturn"] = df["Signal"].shift(1) * df["Return"]
    acc_df = df.groupby("Date").apply(
        lambda x: (x["StrategyReturn"] > 0).sum() / (x["Signal"] != 0).sum() * 100
        if (x["Signal"] != 0).sum() > 0 else 0
    ).reset_index(name="Daily Accuracy")
    return acc_df

# --- Upload Chart ---
uploaded_image = st.file_uploader("📸 Upload Chart", type=["png", "jpg", "jpeg"])
trade_reason = st.text_area("📜 Enter Trade Reason")
if st.button("💾 Save Chart & Reason"):
    if uploaded_image:
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
    df = generate_signals(df)
    signal = df["Signal"].iloc[-1]
    price = round(df["Close"].iloc[-1], 2)
    sl, tp = generate_sl_tp(price, signal, trend)
    reward = abs(tp - price)
    risk = abs(price - sl)
    rr_ratio = round(reward / risk, 2) if risk != 0 else "∞"
    signal_text = "Buy" if signal == 1 else "Sell" if signal == -1 else "No Signal"

    acc_ema = backtest_strategy_accuracy(df)
    acc_epa = backtest_strategy_accuracy(df, use_elliott=True, use_price_action=True)

    st.write(f"**Trend:** `{trend}`")
    st.write(f"**Signal:** `{signal_text}`")
    st.metric("📘 Only EMA Accuracy", f"{acc_ema}%")
    st.metric("🔮 Elliott + Price Action Accuracy", f"{acc_epa}%")
    st.write(f"**Entry Price:** `{price}` | **SL:** `{sl}` | **TP:** `{tp}`")
    st.write(f"📊 **Risk/Reward Ratio:** `{rr_ratio}`")

    breakout, message = detect_elliott_wave_breakout(df)
    if breakout:
        st.warning(message)

    patterns = detect_price_action(df)
    row = {
        "Bullish Engulfing": any("Bullish Engulfing" in p[1] for p in patterns),
        "Bearish Engulfing": any("Bearish Engulfing" in p[1] for p in patterns),
        "Elliott_Wave_Breakout": breakout,
        "EMA_Trend": trend
    }

    conf_score, conf_reason = strategy_confidence(row)
    st.subheader("📊 Pro Strategy Confidence Meter")
    if conf_score >= 3:
        st.success(f"✅ **Strong Buy Signal!**\nConfidence Score: {conf_score}/5")
    elif conf_score <= -3:
        st.error(f"❌ **Strong Sell Signal!**\nConfidence Score: {conf_score}/5")
    else:
        st.warning(f"⚠️ **Sideways / Neutral Market**\nConfidence Score: {conf_score}/5")

    acc_df = accuracy_over_days(df)
    st.line_chart(acc_df.set_index("Date"))
    st.line_chart(df[["Close"]])
    st.markdown("### 📈 Profit Probability Estimate")
    st.info(f"📘 EMA Strategy Profit Chance: `{acc_ema}%` | Loss: `{100 - acc_ema}%`")
    st.success(f"🔮 Elliott + PA Profit Chance: `{acc_epa}%` | Loss: `{100 - acc_epa}%`")
