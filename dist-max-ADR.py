import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# List of tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS', 'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

# Streamlit Title
st.title("Stock Last Price Revisited (Historical Match Excluding Today)")
st.write("Fetch the last adjusted close price of each ticker and find the most recent date before today when it closed at the same price.")

@st.cache
def fetch_data(ticker):
    # Fetch all available historical data for the ticker
    stock_data = yf.download(ticker, period="max")
    return stock_data

@st.cache
def get_last_price_date(ticker):
    # Fetch data for the ticker
    data = fetch_data(ticker)
    
    # Get the last adjusted close price (today's price)
    last_price = data['Adj Close'][-1]
    
    # Exclude the most recent date (today) from the search
    data_before_today = data.iloc[:-1]
    
    # Find the most recent date the stock closed at today's price, excluding today
    matching_dates = data_before_today[data_before_today['Adj Close'] == last_price].index
    
    if len(matching_dates) > 0:
        last_matched_date = matching_dates[-1]
        return last_price, last_matched_date
    else:
        return last_price, None

# Prepare to store results
ticker_data = []

# Loop through each ticker to get the last price and date
for ticker in tickers:
    try:
        last_price, last_date = get_last_price_date(ticker)
        if last_date:
            # Calculate days since the last matched date
            days_since = (datetime.now() - last_date).days
            ticker_data.append({
                'Ticker': ticker,
                'Last Price': last_price,
                'Last Date': last_date.date(),
                'Days Since': days_since
            })
        else:
            ticker_data.append({
                'Ticker': ticker,
                'Last Price': last_price,
                'Last Date': 'No match found',
                'Days Since': None
            })
    except Exception as e:
        st.write(f"Error fetching data for {ticker}: {e}")

# Convert data into DataFrame
df = pd.DataFrame(ticker_data)

# Filter out tickers without matching date
df_valid = df.dropna(subset=['Days Since'])

# Display DataFrame
st.subheader("Stock Data with Last Matched Price Before Today")
st.dataframe(df)

# Plot the time lapsed in a bar plot
if not df_valid.empty:
    st.subheader("Time Lapsed Since Last Price Match (in days)")
    fig = px.bar(df_valid, x='Days Since', y='Ticker', orientation='h', color='Days Since',
                 color_continuous_scale='Viridis', labels={'Days Since': 'Days Since Last Matched Price'})
    st.plotly_chart(fig)
else:
    st.write("No data available for plotting.")
