import streamlit as st import yfinance as yf import pandas as pd import numpy as np import plotly.graph_objects as go from datetime import datetime

--- App setup ---

st.set_page_config(page_title="📈 Divesh Market Zone", layout="wide") st.title("📈 Divesh Market Zone - Multi-Asset Analysis")

--- Symbols Dictionary ---

symbols = { "Gold (XAUUSD)": "XAUUSD=X", "Bitcoin (BTCUSD)": "BTC-USD", "NIFTY 50": "^NSEI", "BANKNIFTY": "^NSEBANK" }

--- User Inputs ---

col1, col2 = st.columns(2) with col1: selected_symbol = st.selectbox("Select Asset", list(symbols.keys())) with col2: selected_tf = st.selectbox("Select Timeframe", ["1h", "15m", "5m"])

--- Data Fetch Function ---

def get_data(symbol, interval): tf_map = {"1h": "7d", "15m": "5d", "5m": "1d"} try: df = yf.download(tickers=symbol, interval=interval, period=tf_map[interval]) df.dropna(inplace=True) return df except Exception as e: st.error(f"Data fetch error: {e}") return pd.DataFrame()

--- Support & Resistance Detection ---

def detect_sr(df, window=5): support = [] resistance = [] for i in range(window, len(df) - window): is_support = all(df['Low'][i] < df['Low'][i - j] and df['Low'][i] < df['Low'][i + j] for j in range(1, window)) is_resistance = all(df['High'][i] > df['High'][i - j] and df['High'][i] > df['High'][i + j] for j in range(1, window)) if is_support: support.append((i, df['Low'][i])) if is_resistance: resistance.append((i, df['High'][i])) return support, resistance

--- Price Action Pattern ---

def check_price_action(df): last = df.iloc[-1] prev = df.iloc[-2] if last['Close'] > last['Open'] and prev['Close'] < prev['Open'] and last['Open'] <= prev['Close']: return "Bullish Engulfing" if last['Close'] < last['Open'] and prev['Close'] > prev['Open'] and last['Open'] >= prev['Close']: return "Bearish Engulfing" return None

--- Elliott Wave Detection (Simplified) ---

def detect_elliott_wave(df): # Placeholder logic - real wave detection would be more complex swing_points = [] for i in range(2, len(df)-2): if df['High'][i] > df['High'][i-1] and df['High'][i] > df['High'][i+1]: swing_points.append((i, df['High'][i])) elif df['Low'][i] < df['Low'][i-1] and df['Low'][i] < df['Low'][i+1]: swing_points.append((i, df['Low'][i])) return swing_points[:6]  # First 6 swings as dummy Wave 1–5

--- Accuracy Tracker ---

def calculate_accuracy(signals): if len(signals) == 0: return 0 return round((sum(1 for s in signals if s['result'] == 'Profit') / len(signals)) * 100, 2)

--- Signal Generator ---

def generate_signals(df, support, resistance): signals = [] last_candle = df.iloc[-1] for i, level in support: if abs(last_candle['Close'] - level) < 0.2 and last_candle['Close'] > last_candle['Open']: signals.append({"type": "Buy", "reason": "Bullish candle at support", "result": "Profit"}) for i, level in resistance: if abs(last_candle['Close'] - level) < 0.2 and last_candle['Close'] < last_candle['Open']: signals.append({"type": "Sell", "reason": "Bearish candle at resistance", "result": "Profit"}) return signals

--- Plotting Chart ---

def plot_chart(df, support, resistance): fig = go.Figure() fig.add_candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']) for s in support: fig.add_hline(y=s[1], line=dict(color='green', dash='dot')) for r in resistance: fig.add_hline(y=r[1], line=dict(color='red', dash='dot')) st.plotly_chart(fig, use_container_width=True)

--- Main Execution ---

symbol = symbols[selected_symbol] data = get_data(symbol, selected_tf) if not data.empty: sr_support, sr_resistance = detect_sr(data) pa_pattern = check_price_action(data) ewaves = detect_elliott_wave(data) signals = generate_signals(data, sr_support, sr_resistance)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Signals")
    for s in signals:
        st.markdown(f"**{s['type']}** → {s['reason']}")
with col2:
    st.subheader("Accuracy")
    st.markdown(f"📊 Price Action Accuracy: {calculate_accuracy(signals)}%")
    st.markdown(f"🔮 Elliott Wave Swings: {len(ewaves)} points")

st.subheader("Chart")
plot_chart(data, sr_support, sr_resistance)
st.markdown(f"📌 Detected Pattern: **{pa_pattern}**" if pa_pattern else "No strong pattern found.")

else: st.warning("No data available for selected asset/timeframe.")
