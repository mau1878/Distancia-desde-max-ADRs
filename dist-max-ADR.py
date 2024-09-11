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
    try:
        st.write(f"Fetching data for {ticker}...")
        # Fetch data for a long range
        stock_data = yf.download(ticker, start="1900-01-01", end=datetime.now().strftime('%Y-%m-%d'))
        
        if stock_data.empty:
            st.warning(f"No data found for {ticker}.")
            return pd.DataFrame()  # Return empty DataFrame if there's no data
        
        st.write(f"Data for {ticker} retrieved successfully.")
        return stock_data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()  # Return empty DataFrame if there's an error

def get_last_price_date(ticker):
    data = fetch_data(ticker)
    
    if data.empty:
        return None, None, None
    
    data.sort_index(inplace=True)
    
    today = datetime.now().date()
    st.write(f"Today's date: {today}")
    
    # Check if today's price is available
    data_today = data[data.index.date == today]
    
    if not data_today.empty:
        today_price = data_today['Adj Close'].iloc[0]
    else:
        today_price = None
    
    st.write(f"Today's price for {ticker}: {today_price}")
    
    # Data before today
    data_before_today = data[data.index.date < today]
    
    if today_price is not None:
        # Filter dates where price is >= today's price
        matching_dates = data_before_today[data_before_today['Adj Close'] >= today_price].index
        
        st.write(f"Matching dates for {ticker}: {matching_dates}")
        
        if len(matching_dates) > 0:
            last_matched_date = matching_dates[-1]
            price_at_last_matched_date = data.loc[last_matched_date, 'Adj Close']
            st.write(f"Last matched date: {last_matched_date}, Price at last matched date: {price_at_last_matched_date}")
            return today_price, last_matched_date, price_at_last_matched_date
        else:
            return today_price, None, None
    else:
        return None, None, None

ticker_data = []

for ticker in tickers:
    st.write(f"Processing ticker: {ticker}")
    try:
        today_price, last_date, price_at_last_date = get_last_price_date(ticker)
        if today_price is None:
            st.write(f"No data found for {ticker}.")
            continue
        
        if last_date:
            days_since = (datetime.now().date() - last_date.date()).days
            ticker_data.append({
                'Ticker': ticker,
                'Last Price (Today)': today_price,
                'Last Date': last_date.to_pydatetime(),
                'Price at Last Date': price_at_last_date,
                'Days Since': days_since
            })
        else:
            ticker_data.append({
                'Ticker': ticker,
                'Last Price (Today)': today_price,
                'Last Date': 'No match found',
                'Price at Last Date': 'N/A',
                'Days Since': None
            })
    except Exception as e:
        st.error(f"Error processing data for {ticker}: {e}")

df = pd.DataFrame(ticker_data)

st.subheader("Stock Data with Last Matched Price or Higher Before Today")
st.dataframe(df)

# Filter out tickers without valid 'Days Since'
if 'Days Since' in df.columns:
    df_valid = df.dropna(subset=['Days Since'])
else:
    df_valid = df

if not df_valid.empty:
    st.subheader("Time Lapsed Since Last Price Match or Higher (in days)")
    fig = px.bar(df_valid, x='Days Since', y='Ticker', orientation='h', color='Days Since',
                 color_continuous_scale='Viridis', labels={'Days Since': 'Days Since Last Matched Price'})
    st.plotly_chart(fig)
else:
    st.write("No data available for plotting.")
