import streamlit as st
from PIL import Image
import pandas as pd
import base64
import matplotlib.pyplot as plt
import requests
import json

# ----------------- CONFIG ------------------

API_KEY = "API_KEY"

# -------------------------------------------

# Page layout
st.set_page_config(layout="wide")
st.title('Crypto Price App')
st.markdown("""
This app retrieves cryptocurrency prices for the top 100 coins from **CoinMarketCap** using its public API.
""")

# About section
with st.expander("About"):
    st.markdown("""
    * **Libraries:** base64, pandas, streamlit, matplotlib, requests, json
    * **Data Source:** [CoinMarketCap API](https://coinmarketcap.com/api/)
    * **Author:** Adapted from the original web scraper project by Bryan Feng.
    """)

col1 = st.sidebar
col2, col3 = st.columns((2, 1))

col1.header('Input Options')

# Currency selection
currency_price_unit = col1.selectbox('Select currency for price', ('USD', 'BTC', 'ETH'))

# ----------------- LOAD DATA ------------------

@st.cache_data
def load_data(currency='USD'):
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }
    parameters = {
        'start': '1',
        'limit': '100',
        'convert': currency
    }

    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()

    coin_data = data['data']

    coin_name, coin_symbol, market_cap = [], [], []
    percent_change_1h, percent_change_24h, percent_change_7d = [], [], []
    price, volume_24h = [], []

    for coin in coin_data:
        coin_name.append(coin['name'])
        coin_symbol.append(coin['symbol'])
        price.append(coin['quote'][currency]['price'])
        percent_change_1h.append(coin['quote'][currency]['percent_change_1h'])
        percent_change_24h.append(coin['quote'][currency]['percent_change_24h'])
        percent_change_7d.append(coin['quote'][currency]['percent_change_7d'])
        market_cap.append(coin['quote'][currency]['market_cap'])
        volume_24h.append(coin['quote'][currency]['volume_24h'])

    df = pd.DataFrame({
        'coin_name': coin_name,
        'coin_symbol': coin_symbol,
        'price': price,
        'percentChange1h': percent_change_1h,
        'percentChange24h': percent_change_24h,
        'percentChange7d': percent_change_7d,
        'marketCap': market_cap,
        'volume24h': volume_24h,
    })

    return df

df = load_data(currency_price_unit)

if df.empty:
    st.warning("No data fetched. Check API key or internet connection.")
    st.stop()

# ----------------- UI OPTIONS ------------------

sorted_coin = sorted(df['coin_symbol'])
selected_coin = col1.multiselect('Cryptocurrency', sorted_coin, sorted_coin)

df_selected_coin = df[df['coin_symbol'].isin(selected_coin)]

num_coin = col1.slider('Display Top N Coins', 1, 100, 100)
df_coins = df_selected_coin[:num_coin]

percent_timeframe = col1.selectbox('Percent change time frame', ['7d', '24h', '1h'])
percent_dict = {"7d": 'percentChange7d', "24h": 'percentChange24h', "1h": 'percentChange1h'}
selected_percent_timeframe = percent_dict[percent_timeframe]

sort_values = col1.selectbox('Sort values?', ['Yes', 'No'])

# ----------------- MAIN DISPLAY ------------------

col2.subheader('Price Data of Selected Cryptocurrency')
col2.write(f'Data Dimension: {df_selected_coin.shape[0]} rows and {df_selected_coin.shape[1]} columns.')
col2.dataframe(df_coins)

# Download CSV
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="crypto.csv">Download CSV File</a>'
    return href

col2.markdown(filedownload(df_selected_coin), unsafe_allow_html=True)

# Table of % Price Change
col2.subheader('Table of % Price Change')
df_change = pd.concat([
    df_coins['coin_symbol'],
    df_coins['percentChange1h'],
    df_coins['percentChange24h'],
    df_coins['percentChange7d']
], axis=1)
df_change = df_change.set_index('coin_symbol')
df_change['positive_percent_change_1h'] = df_change['percentChange1h'] > 0
df_change['positive_percent_change_24h'] = df_change['percentChange24h'] > 0
df_change['positive_percent_change_7d'] = df_change['percentChange7d'] > 0
col2.dataframe(df_change)

# ----------------- BAR PLOT ------------------

col3.subheader('Bar plot of % Price Change')

if percent_timeframe == '7d':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percentChange7d'])
    col3.write('*7 days period*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percentChange7d'].plot(kind='barh', color=df_change['positive_percent_change_7d'].map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
elif percent_timeframe == '24h':
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percentChange24h'])
    col3.write('*24 hour period*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percentChange24h'].plot(kind='barh', color=df_change['positive_percent_change_24h'].map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
else:
    if sort_values == 'Yes':
        df_change = df_change.sort_values(by=['percentChange1h'])
    col3.write('*1 hour period*')
    plt.figure(figsize=(5, 25))
    plt.subplots_adjust(top=1, bottom=0)
    df_change['percentChange1h'].plot(kind='barh', color=df_change['positive_percent_change_1h'].map({True: 'g', False: 'r'}))
    col3.pyplot(plt)
