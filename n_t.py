import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
import os
from PIL import Image

st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide")
st.title("📈 Divesh Market Zone - Swing + Intraday + Futures Analysis")

# --- Create Save Folder ---
if not os.path.exists("saved_charts"):
    os.makedirs("saved_charts")

# --- Symbols Dictionary ---
symbols = {
    "Bitcoin (BTC)": "BTC-USD",
    "Gold (XAUUSD)": "XAUUSD=X",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "Reliance Industries": "RELIANCE.NS",
    "Tata Consultancy Services": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Axis Bank": "AXISBANK.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Larsen & Toubro": "LT.NS",
    "ITC Ltd": "ITC.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Wipro": "WIPRO.NS",
    "NTPC": "NTPC.NS",
    "ONGC": "ONGC.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Titan Company": "TITAN.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Tech Mahindra": "TECHM.NS",
    "Adani Ports": "ADANIPORTS.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "Power Grid": "POWERGRID.NS"
}

# --- Timeframes ---
timeframes = {
    "1 Hour": "60m",
    "15 Minutes": "15m",
    "5 Minutes": "5m"
}

# --- Functions ---
def get_data(symbol, interval):
    return yf.download(tickers=symbol, period="7d", interval=interval, progress=False)

def detect_trend(df):
    ema20 = df['Close'].ewm(span=20).mean()
    ema50 = df['Close'].ewm(span=50).mean()
    return "Uptrend" if ema20.iloc[-1] > ema50.iloc[-1] else "Downtrend"

def detect_elliott_wave_breakout(df):
    recent_close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-10]
    breakout = recent_close > prev_close * 1.02 or recent_close < prev_close * 0.98
    msg = "📈 Elliott Wave breakout detected!" if breakout else ""
    return breakout, msg

def detect_price_action(df):
    patterns = []
    for i in range(2, len(df)):
        prev, curr = df.iloc[i-1], df.iloc[i]
        if curr['Close'] > curr['Open'] and prev['Close'] < prev['Open'] and curr['Close'] > prev['Open'] and curr['Open'] < prev['Close']:
            patterns.append((df.index[i], "Bullish Engulfing"))
        elif curr['Close'] < curr['Open'] and prev['Close'] > prev['Open'] and curr['Open'] > prev['Close'] and curr['Close'] < prev['Open']:
            patterns.append((df.index[i], "Bearish Engulfing"))
    return patterns

def strategy_confidence(row):
    score = 0
    reasons = []
    if row["Bullish Engulfing"]:
        score += 1
        reasons.append("Bullish Engulfing")
    if row["Bearish Engulfing"]:
        score -= 1
        reasons.append("Bearish Engulfing")
    if row["Elliott_Wave_Breakout"]:
        score += 1
        reasons.append("Elliott Wave Breakout")
    if row["EMA_Trend"] == "Uptrend":
        score += 1
        reasons.append("EMA Uptrend")
    elif row["EMA_Trend"] == "Downtrend":
        score -= 1
        reasons.append("EMA Downtrend")
    return score, ", ".join(reasons)

def generate_signals(df, use_elliott=False, use_price_action=False):
    df['EMA20'] = df['Close'].ewm(span=20).mean()
    df['EMA50'] = df['Close'].ewm(span=50).mean()
    df['Signal'] = 0
    trend = detect_trend(df)
    if trend == "Uptrend":
        df.loc[df['EMA20'] > df['EMA50'], 'Signal'] = 1
    elif trend == "Downtrend":
        df.loc[df['EMA20'] < df['EMA50'], 'Signal'] = -1
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
    return df

def backtest_strategy_accuracy(df, use_elliott=False, use_price_action=False):
    df = generate_signals(df, use_elliott, use_price_action)
    total_signals = df[df['Signal'] != 0]
    correct = df[df['StrategyReturn'] > 0]
    accuracy = round(len(correct) / len(total_signals) * 100, 2) if len(total_signals) else 0
    return accuracy

def accuracy_over_days(df):
    df = df.copy()
    df['Date'] = df.index.date
    df = generate_signals(df)
    accuracy_df = df.groupby('Date').apply(
        lambda x: (x['StrategyReturn'] > 0).sum() / (x['Signal'] != 0).sum() * 100
        if (x['Signal'] != 0).sum() > 0 else 0
    ).reset_index(name="Daily Accuracy")
    return accuracy_df

def generate_sl_tp(price, signal, trend):
    sl = price * 0.99 if signal == 1 else price * 1.01
    tp = price * 1.02 if signal == 1 else price * 0.98
    return round(sl, 2), round(tp, 2)

# --- UI Section ---
selected_symbol = st.selectbox("📌 Select Asset", list(symbols.keys()))
symbol_yf = symbols[selected_symbol]

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
    df = generate_signals(df)

    if not df[df["Signal"] != 0].empty:
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
    st.markdown("### 📈 Profit Probability Estimate")
    st.info(f"📘 **EMA Strategy Profit Chance:** `{acc_ema}%` | Loss: `{100 - acc_ema}%`")
    st.success(f"🔮 **Elliott + PA Strategy Profit Chance:** `{acc_epa}%` | Loss: `{100 - acc_epa}%`")
