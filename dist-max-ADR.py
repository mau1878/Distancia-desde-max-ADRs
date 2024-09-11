import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# List of tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS', 'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

# Streamlit Title
st.title("Stock Last Price Revisited (Historical Match Including Higher Prices)")
st.write("Fetch the last adjusted close price of each ticker and find the most recent date before today when it closed at that price or a higher one, including historical data from previous years.")

@st.cache_data
def fetch_data(ticker):
    # Fetch all available historical data for the ticker
    try:
        stock_data = yf.download(ticker, start="1900-01-01", end=datetime.now().strftime('%Y-%m-%d'))
        if stock_data.empty:
            st.warning(f"No data found for {ticker}.")
        return stock_data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()  # Return empty DataFrame if there's an error

def get_last_price_date(ticker):
    # Fetch data for the ticker
    data = fetch_data(ticker)
    
    if data.empty:
        return None, None, None  # Return None if no data was retrieved
    
    # Ensure the data is sorted by date
    data.sort_index(inplace=True)
    
    # Get today's date and adjusted close price
    today = datetime.now().date()
    data_today = data[data.index.date == today]

    # Check if today's price is available
    if not data_today.empty:
        today_price = data_today['Adj Close'].iloc[0]
    else:
        today_price = None

    # Exclude the most recent date if it is today
    data_before_today = data[data.index.date < today]
    
    if today_price is not None:
        # Find the last date where the price was at or above today's price
        matching_dates = data_before_today[data_before_today['Adj Close'] >= today_price].index
        
        if len(matching_dates) > 0:
            last_matched_date = matching_dates[-1]  # Get the last matching date
            price_at_last_matched_date = data['Adj Close'].loc[last_matched_date]  # Price at that date
            return today_price, last_matched_date, price_at_last_matched_date
        else:
            return today_price, None, None
    else:
        return None, None, None

# Prepare to store results
ticker_data = []

# Loop through each ticker to get the last price, date, and price at the matching date
for ticker in tickers:
    st.write(f"Fetching data for: {ticker}")  # Diagnostic message
    try:
        today_price, last_date, price_at_last_date = get_last_price_date(ticker)
        if today_price is None:
            st.write(f"No data found for {ticker}.")  # Show if no data is found
            continue
        
