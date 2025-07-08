# crypto_dashboard.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

# --------------------- Page Config ---------------------
st.set_page_config(page_title="Crypto Price App", layout="wide")
st.title("Crypto Price App")
st.markdown("This app retrieves cryptocurrency prices from **CoinGecko API** (no API key required).")

# --------------------- Sidebar ---------------------
st.sidebar.header("Options")
currency = st.sidebar.selectbox("Select currency", ("usd", "btc", "eth"))
per_page = st.sidebar.slider("Number of coins", 10, 100, 50)
sort_order = st.sidebar.selectbox("Sort by", (
    "market_cap_desc", "market_cap_asc", "volume_desc", "volume_asc"
))
sort_values = st.sidebar.selectbox("Sort values?", ("Yes", "No"))
timeframe = st.sidebar.selectbox("Percent change timeframe", ("1h", "24h", "7d"))

# --------------------- Load Data ---------------------
@st.cache_data
def load_data(currency="usd", per_page=50, sort="market_cap_desc"):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": currency,
        "order": sort,
        "per_page": per_page,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d"
    }
    r = requests.get(url, params=params)
    data = r.json()
    return pd.DataFrame(data)

df = load_data(currency, per_page, sort_order)

# --------------------- Coin Selection ---------------------
all_symbols = df["symbol"].str.upper().tolist()
selected_symbols = st.sidebar.multiselect("Select cryptocurrencies", all_symbols, default=all_symbols)

df_filtered = df[df["symbol"].str.upper().isin(selected_symbols)]

# --------------------- Layout Columns ---------------------
col2, col3 = st.columns([2, 1])

# --------------------- Table ---------------------
col2.subheader("Price Data")
columns_to_show = [
    "name", "symbol", "current_price", "market_cap",
    "price_change_percentage_1h_in_currency",
    "price_change_percentage_24h_in_currency",
    "price_change_percentage_7d_in_currency"
]
columns_available = [col for col in columns_to_show if col in df_filtered.columns]
col2.write(f"Data Dimension: {df_filtered.shape[0]} rows × {df_filtered.shape[1]} columns")
col2.dataframe(df_filtered[columns_available])

# --------------------- Download CSV ---------------------
def download_csv(df):
    return df.to_csv(index=False).encode("utf-8")

col2.download_button(
    label="📥 Download Data as CSV",
    data=download_csv(df_filtered),
    file_name="crypto_prices.csv",
    mime="text/csv"
)

# --------------------- Bar Chart ---------------------
col3.subheader(f"{timeframe} Price Change Chart")

timeframe_col = {
    "1h": "price_change_percentage_1h_in_currency",
    "24h": "price_change_percentage_24h_in_currency",
    "7d": "price_change_percentage_7d_in_currency"
}[timeframe]

if timeframe_col in df_filtered.columns:
    df_chart = df_filtered.copy()

    if sort_values == "Yes":
        df_chart = df_chart.sort_values(by=[timeframe_col])

    colors = df_chart[timeframe_col].apply(lambda x: "g" if x >= 0 else "r")
    plt.figure(figsize=(6, len(df_chart) / 2))
    plt.barh(df_chart["symbol"].str.upper(), df_chart[timeframe_col], color=colors)
    plt.xlabel("% Change")
    plt.title(f"{timeframe} Price Change (%)")
    col3.pyplot(plt)
else:
    col3.warning(f"{timeframe_col} not available in data.")
