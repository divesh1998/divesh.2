Final Full Code with:

- Scalping (EMA10/EMA20)

- Trend Detection (EMA20 vs EMA50)

- Price Action

- Full Elliott Wave Detection with Fibonacci (1H and 15M only)

import yfinance as yf import pandas as pd import streamlit as st from datetime import datetime import os from PIL import Image

st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide") st.title(":chart_with_upwards_trend: Divesh Market Zone")

--- Create save folder ---

if not os.path.exists("saved_charts"): os.makedirs("saved_charts")

--- Symbols ---

symbols = { "Bitcoin (BTC)": "BTC-USD", "Gold (XAU)": "GC=F" } symbol = st.selectbox("Select Asset", list(symbols.keys())) symbol_yf = symbols[symbol] timeframes = {"1H": "1h", "15M": "15m", "5M": "5m"}

--- Fetch Data ---

def get_data(symbol, interval, period='7d'): df = yf.download(symbol, interval=interval, period=period) if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0) df.dropna(inplace=True) return df

--- Trend Detection ---

def detect_trend(df): df['EMA20'] = df['Close'].ewm(span=20).mean() df['EMA50'] = df['Close'].ewm(span=50).mean() ema_diff = df['EMA20'] - df['EMA50'] if ema_diff.iloc[-1] > 0 and ema_diff.iloc[-2] > 0 and ema_diff.iloc[-3] > 0: return "Uptrend" elif ema_diff.iloc[-1] < 0 and ema_diff.iloc[-2] < 0 and ema_diff.iloc[-3] < 0: return "Downtrend" else: return "Sideways"

--- Scalping Signals ---

def generate_scalping_signals(df): df['EMA10'] = df['Close'].ewm(span=10).mean() df['EMA20'] = df['Close'].ewm(span=20).mean() df['Signal'] = 0 for i in range(1, len(df)): if df['EMA10'].iloc[i] > df['EMA20'].iloc[i] and df['EMA10'].iloc[i-1] <= df['EMA20'].iloc[i-1]: df.at[df.index[i], 'Signal'] = 1 elif df['EMA10'].iloc[i] < df['EMA20'].iloc[i] and df['EMA10'].iloc[i-1] >= df['EMA20'].iloc[i-1]: df.at[df.index[i], 'Signal'] = -1 return df

--- Price Action (basic) ---

def detect_price_action(df): patterns = [] for i in range(2, len(df)): o1, c1 = df.iloc[i-1][["Open", "Close"]] o2, c2 = df.iloc[i][["Open", "Close"]] if c1 < o1 and c2 > o2 and c2 > o1 and o2 < c1: patterns.append((df.index[i], "Bullish Engulfing")) elif c1 > o1 and c2 < o2 and c2 < o1 and o2 > c1: patterns.append((df.index[i], "Bearish Engulfing")) return patterns

--- Elliott Wave + Fibonacci ---

def detect_elliott_waves(df): def find_swing_points(data, lookback=5): highs = data['High'] lows = data['Low'] swing_highs = [] swing_lows = [] for i in range(lookback, len(data)-lookback): if highs[i] == max(highs[i-lookback:i+lookback]): swing_highs.append((data.index[i], highs[i])) if lows[i] == min(lows[i-lookback:i+lookback]): swing_lows.append((data.index[i], lows[i])) return swing_highs, swing_lows

def fib_ratio(a, b):
    return round(abs((b - a) / a) * 100, 2) if a != 0 else 0

swing_highs, swing_lows = find_swing_points(df)
if len(swing_lows) < 6 or len(swing_highs) < 6:
    return False, "Not enough swing points", []

wave1 = swing_lows[-6][1], swing_highs[-5][1]
wave2 = swing_lows[-4][1]
wave3 = swing_highs[-3][1]
wave4 = swing_lows[-2][1]
wave5 = swing_highs[-1][1]

fib_valid = []
retrace_w2 = fib_ratio(wave1[1], wave2)
if 45 <= retrace_w2 <= 65:
    fib_valid.append("Wave 2: 50–61.8% retracement")

ext_w3 = fib_ratio(wave1[1], wave3)
if ext_w3 >= 150:
    fib_valid.append("Wave 3: >161.8% extension")

retrace_w4 = fib_ratio(wave3, wave4)
if 30 <= retrace_w4 <= 42:
    fib_valid.append("Wave 4: ~38% retracement")

ext_w5 = fib_ratio(wave1[1], wave5)
if 80 <= ext_w5 <= 120:
    fib_valid.append("Wave 5: Equal to Wave 1")

message = "🌀 Elliott Wave structure with Fibonacci match!" if fib_valid else "Wave structure weak"
return True, message, fib_valid

--- SL/TP ---

def generate_sl_tp(price, signal, trend): atr = 0.015 if trend == "Uptrend" else 0.02 rr = 2.0 if signal == 1: sl = price * (1 - atr) tp = price + (price - sl) * rr elif signal == -1: sl = price * (1 + atr) tp = price - (sl - price) * rr else: sl = tp = price return round(sl, 2), round(tp, 2)

--- Accuracy ---

def backtest_scalping_accuracy(df): df = generate_scalping_signals(df) df['Return'] = df['Close'].pct_change().shift(-1) df['StrategyReturn'] = df['Signal'].shift(1) * df['Return'] total_signals = df[df['Signal'] != 0] correct = df[df['StrategyReturn'] > 0] accuracy = round(len(correct) / len(total_signals) * 100, 2) if len(total_signals) else 0 return accuracy

--- Upload Chart ---

uploaded_image = st.file_uploader(":camera: Upload Chart", type=["png", "jpg", "jpeg"]) trade_reason = st.text_area(":scroll: Enter Trade Reason") if st.button(":floppy_disk: Save Chart & Reason"): if uploaded_image is not None: filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_image.name}" filepath = os.path.join("saved_charts", filename) with open(filepath, "wb") as f: f.write(uploaded_image.read()) with open(filepath + ".txt", "w", encoding="utf-8") as f: f.write(trade_reason) st.success("Chart and Reason Saved!")

--- Show Saved Charts ---

st.subheader(":file_folder: Saved Charts") for file in os.listdir("saved_charts"): if file.lower().endswith((".png", ".jpg", ".jpeg")): st.image(os.path.join("saved_charts", file), width=350) txt_file = os.path.join("saved_charts", file + ".txt") if os.path.exists(txt_file): with open(txt_file, "r", encoding="utf-8") as f: reason = f.read() st.caption(f":scroll: Reason: {reason}")

--- Multi-Timeframe Analysis ---

for tf_label, tf_code in timeframes.items(): st.markdown("---") st.subheader(f"🕒 Timeframe: {tf_label}")

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
    signal = 0
    price = round(df["Close"].iloc[-1], 2)

sl, tp = generate_sl_tp(price, signal, trend)
rr_ratio = round(abs(tp - price) / abs(price - sl), 2) if abs(price - sl) != 0 else "∞"
signal_text = "🟢 Buy" if signal == 1 else "🔴 Sell" if signal == -1 else "⚪ No Signal"
accuracy = backtest_scalping_accuracy(df)

st.write(f"**Trend:** `{trend}`")
st.write(f"**Signal:** `{signal_text}`")
st.metric("🎯 Scalping Strategy Accuracy", f"{accuracy}%")
st.write(f"**Entry Price:** `{price}` | **SL:** `{sl}` | **TP:** `{tp}`")
st.write(f"📊 **Risk/Reward Ratio:** `{rr_ratio}`")

if tf_label in ["15M", "5M"]:
    if trend == "Sideways":
        label = '<span style="color:orange; font-weight:bold;">⚠️ Scalping Zone (Sideways)</span>'
    else:
        label = '<span style="color:green; font-weight:bold;">✅ Trend Zone (Scalping Allowed)</span>'
    st.markdown(f"**Scalping Status:** {label}", unsafe_allow_html=True)

if tf_label in ["1H", "15M"]:
    ew_detected, ew_msg, fib_info = detect_elliott_waves(df)
    if ew_detected:
        st.info(ew_msg)
        for note in fib_info:
            st.success(note)

# --- Price Action Info ---
pa_patterns = detect_price_action(df)
if pa_patterns:
    st.markdown("### 🔍 Price Action Patterns Detected:")
    for dt, pattern in pa_patterns[-3:]:
        st.write(f"{dt} - `{pattern}`")

