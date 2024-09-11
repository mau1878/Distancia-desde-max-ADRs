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
        return None, None  # Return None if no data was retrieved
    
    # Ensure the data is sorted by date
    data.sort_index(inplace=True)
    
    # Get the last adjusted close price (most recent price)
    last_price = data['Adj Close'].iloc[-1]
    
    # Exclude the most recent date if it is today
    data_before_today = data[data.index.date < datetime.now().date()]
    
    # Debug output
    st.write(f"Last adjusted close price for {ticker}: {last_price}")
    st.write(f"Data before today for {ticker}:\n", data_before_today.head())
    
    # Find the last date where the price was at or above the last price
    matching_dates = data_before_today[data_before_today['Adj Close'] >= last_price].index
    
    # Debug output
    st.write(f"Matching dates for {ticker}:\n", matching_dates)

    if len(matching_dates) > 0:
        last_matched_date = matching_dates[-1]  # Get the last matching date
        return last_price, last_matched_date
    else:
        return last_price, None

# Prepare to store results
ticker_data = []

# Loop through each ticker to get the last price and date
for ticker in tickers:
    st.write(f"Fetching data for: {ticker}")  # Diagnostic message
    try:
        last_price, last_date = get_last_price_date(ticker)
        if last_price is None:
            st.write(f"No data found for {ticker}.")  # Show if no data is found
            continue
        
        if last_date:
            # Calculate days since the last matched date
            days_since = (datetime.now() - last_date).days
            ticker_data.append({
                'Ticker': ticker,
                'Last Price': last_price,
                'Last Date': last_date.to_pydatetime(),  # Convert to datetime.datetime
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
        st.error(f"Error processing data for {ticker}: {e}")

# Convert data into DataFrame
df = pd.DataFrame(ticker_data)

# Filter out tickers without matching date
df_valid = df.dropna(subset=['Days Since'])

# Display DataFrame
st.subheader("Stock Data with Last Matched Price or Higher Before Today")
st.dataframe(df)

# Plot the time lapsed in a bar plot
if not df_valid.empty:
    st.subheader("Time Lapsed Since Last Price Match or Higher (in days)")
    fig = px.bar(df_valid, x='Days Since', y='Ticker', orientation='h', color='Days Since',
                 color_continuous_scale='Viridis', labels={'Days Since': 'Days Since Last Matched Price'})
    st.plotly_chart(fig)
else:
    st.write("No data available for plotting.")
