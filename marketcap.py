import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# ====================================
# CONFIG
# ====================================
st.set_page_config(
    page_title="~",
    layout="wide"
)

API_KEY = "d5fd785f412047069ceeb40ca2d6203b"

headers = {
    "Accepts": "application/json",
    "X-CMC_PRO_API_KEY": API_KEY,
}

# ====================================
# TITLE
# ====================================
st.title("~")
st.caption("EMA + RSI + Fibonacci + Support Resistance")

# ====================================
# INPUT COIN
# ====================================
coin_input = st.text_input(
    "Masukkan Coin",
    "BTC,ETH,SOL"
)

coins = [x.strip().upper() for x in coin_input.split(",")]

refresh = st.sidebar.slider(
    "Refresh (detik)",
    1,
    60,
    5
)

# ====================================
# PRICE HISTORY STORAGE
# ====================================
if "history" not in st.session_state:
    st.session_state.history = {}

# ====================================
# GET USD IDR
# ====================================
@st.cache_data(ttl=60)
def get_usd_idr():

    url = "https://open.er-api.com/v6/latest/USD"

    response = requests.get(url)

    data = response.json()

    return data["rates"]["IDR"]

# ====================================
# GET COIN DATA
# ====================================
@st.cache_data(ttl=5)
def get_data(symbols):

    url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest"

    params = {
        "symbol": ",".join(symbols),
        "convert": "USD"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    return response.json()

# ====================================
# EMA
# ====================================
def calculate_ema(prices, period):

    if len(prices) < period:
        return None

    return pd.Series(prices).ewm(
        span=period,
        adjust=False
    ).mean().iloc[-1]

# ====================================
# RSI
# ====================================
def calculate_rsi(prices, period=14):

    if len(prices) < period:
        return None

    delta = np.diff(prices)

    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return round(rsi, 2)

# ====================================
# SUPPORT RESISTANCE
# ====================================
def calculate_sr(price):

    support1 = price * 0.95
    support2 = price * 0.90

    resistance1 = price * 1.05
    resistance2 = price * 1.10

    return (
        support1,
        support2,
        resistance1,
        resistance2
    )

# ====================================
# FIBONACCI
# ====================================
def fibonacci_levels(price):

    high = price * 1.10
    low = price * 0.90

    diff = high - low

    fib_236 = high - diff * 0.236
    fib_382 = high - diff * 0.382
    fib_500 = high - diff * 0.500
    fib_618 = high - diff * 0.618
    fib_786 = high - diff * 0.786

    return (
        fib_236,
        fib_382,
        fib_500,
        fib_618,
        fib_786
    )

# ====================================
# MARKET STATUS
# ====================================
def market_status(price, ema20, ema50, rsi):

    if ema20 is None or ema50 is None or rsi is None:
        return "⌛ Analisa..."

    if price > ema20 and ema20 > ema50 and rsi > 55:
        return "🚀 Bullish"

    elif price < ema20 and ema20 < ema50 and rsi < 45:
        return "🔻 Bearish"

    else:
        return "📊 Sideways"

# ====================================
# MAIN LOOP
# ====================================
placeholder = st.empty()

while True:

    with placeholder.container():

        try:

            usd_to_idr = get_usd_idr()

            data = get_data(coins)

            rows = []

            for symbol in coins:

                if symbol not in data["data"]:
                    continue

                coin = data["data"][symbol][0]

                # =========================
                # PRICE
                # =========================
                price_usd = coin["quote"]["USD"]["price"]

                price_idr = price_usd * usd_to_idr

                change24 = round(
                    coin["quote"]["USD"]["percent_change_24h"],
                    2
                )

                volume = coin["quote"]["USD"]["volume_24h"]

                marketcap = coin["quote"]["USD"]["market_cap"]

                # =========================
                # SAVE HISTORY
                # =========================

                if symbol not in st.session_state.history:

                    # isi history awal
                    st.session_state.history[symbol] = [
                        price_idr * (1 + (i * 0.001))
                        for i in range(60)
                         ]

                st.session_state.history[symbol].append(price_idr)

                if len(st.session_state.history[symbol]) > 100:
                    st.session_state.history[symbol].pop(0)

                prices = st.session_state.history[symbol]

                # =========================
                # EMA
                # =========================
                ema20 = calculate_ema(prices, 20)
                ema50 = calculate_ema(prices, 50)

                # =========================
                # RSI
                # =========================
                rsi = calculate_rsi(prices)

                # =========================
                # SUPPORT RESISTANCE
                # =========================
                s1, s2, r1, r2 = calculate_sr(price_idr)

                # =========================
                # FIBONACCI
                # =========================
                f236, f382, f500, f618, f786 = fibonacci_levels(price_idr)

                # =========================
                # MARKET STATUS
                # =========================
                status = market_status(
                    price_idr,
                    ema20,
                    ema50,
                    rsi
                )

                rows.append({

                    "Coin":
                    symbol,

                    "Harga":
                    f"Rp {price_idr:,.0f}",

                    "24h %":
                    f"{change24}%",

                    "EMA20":
                    f"Rp {ema20:,.0f}" if ema20 else "-",

                    "EMA50":
                    f"Rp {ema50:,.0f}" if ema50 else "-",

                    "RSI":
                    round(rsi, 2) if rsi else "-",

                    "Volume":
                    f"${volume:,.0f}",

                    "Market Cap":
                    f"${marketcap:,.0f}",

                    "Support 1":
                    f"Rp {s1:,.0f}",

                    "Support 2":
                    f"Rp {s2:,.0f}",

                    "Resistance 1":
                    f"Rp {r1:,.0f}",

                    "Resistance 2":
                    f"Rp {r2:,.0f}",

                    "Fib 0.236":
                    f"Rp {f236:,.0f}",

                    "Fib 0.382":
                    f"Rp {f382:,.0f}",

                    "Fib 0.5":
                    f"Rp {f500:,.0f}",

                    "Fib 0.618":
                    f"Rp {f618:,.0f}",

                    "Fib 0.786":
                    f"Rp {f786:,.0f}",

                    "Status":
                    status
                })

            df = pd.DataFrame(rows)

            # ====================================
            # TABLE
            # ====================================
            st.subheader("📊 Market Monitoring")

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.divider()

            # ====================================
            # QUICK VIEW
            # ====================================
            st.subheader("🔥 Quick View")

            cols = st.columns(len(rows))

            for i, row in enumerate(rows):

                with cols[i]:

                    st.metric(
                        row["Coin"],
                        row["Harga"],
                        row["24h %"]
                    )

                    st.write(f"📈 {row['Status']}")

                    st.write(f"EMA20 : {row['EMA20']}")
                    st.write(f"EMA50 : {row['EMA50']}")

                    st.write(f"RSI : {row['RSI']}")

                    st.write("🟢 SUPPORT")
                    st.write(f"S1 : {row['Support 1']}")
                    st.write(f"S2 : {row['Support 2']}")

                    st.write("🔴 RESISTANCE")
                    st.write(f"R1 : {row['Resistance 1']}")
                    st.write(f"R2 : {row['Resistance 2']}")

            st.caption(
                f"⏱ Auto refresh {refresh} detik | "
                f"USD/IDR : Rp {usd_to_idr:,.0f}"
            )

        except Exception as e:
            st.error(f"Error : {e}")

    time.sleep(refresh)

    st.rerun()