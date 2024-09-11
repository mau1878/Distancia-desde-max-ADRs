import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# List of tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS', 'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

st.title("Stock Data with Latest Prices")

@st.cache_data
def fetch_data(ticker, end_date):
    try:
        st.write(f"Fetching data for {ticker}...")
        stock_data = yf.download(ticker, start="1900-01-01", end=end_date)
        
        if stock_data.empty:
            st.warning(f"No data found for {ticker}.")
            return pd.DataFrame()
        
        st.write(f"Data for {ticker} retrieved successfully.")
        st.write(f"Data range for {ticker}: {stock_data.index.min()} to {stock_data.index.max()}")
        return stock_data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def get_latest_price(ticker):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    end_date = tomorrow.strftime('%Y-%m-%d')
    data = fetch_data(ticker, end_date)
    
    if data.empty:
        return None, None, None
    
    data.sort_index(inplace=True)
    
    # Filter data to include entries up to tomorrow
    data_filtered = data[data.index.date <= tomorrow]
    
    if data_filtered.empty:
        return None, None, None
    
    # Find the most recent date available with a price greater than or equal to today's price
    latest_date = data_filtered.index.max().date()
    latest_price = data_filtered['Adj Close'].loc[data_filtered.index.date == latest_date].iloc[-1]
    
    st.write(f"Most recent date for {ticker}: {latest_date}")
    st.write(f"Latest price for {ticker}: {latest_price}")
    
    # Find the last available price before the most recent date
    data_before_latest = data[data.index.date < latest_date]
    
    if not data_before_latest.empty:
        data_before_latest = data_before_latest[data_before_latest['Adj Close'] >= latest_price]
        if not data_before_latest.empty:
            last_matched_date = data_before_latest.index[-1].date()
            price_at_last_matched_date = data_before_latest['Adj Close'].iloc[-1]
            st.write(f"Last matched date: {last_matched_date}, Price at last matched date: {price_at_last_matched_date}")
            return latest_price, last_matched_date, price_at_last_matched_date
        else:
            return latest_price, None, None
    else:
        return latest_price, None, None

ticker_data = []

for ticker in tickers:
    st.write(f"Processing ticker: {ticker}")
    try:
        latest_price, last_date, price_at_last_date = get_latest_price(ticker)
        if latest_price is None:
            st.write(f"No data found for {ticker}.")
            continue
        
        if last_date:
            days_since = (datetime.now().date() - last_date).days
            ticker_data.append({
                'Ticker': ticker,
                'Latest Price': latest_price,
                'Last Date': last_date,
                'Price at Last Date': price_at_last_date,
                'Days Since': days_since
            })
        else:
            ticker_data.append({
                'Ticker': ticker,
                'Latest Price': latest_price,
                'Last Date': 'No match found',
                'Price at Last Date': 'N/A',
                'Days Since': None
            })
    except Exception as e:
        st.error(f"Error processing data for {ticker}: {e}")

df = pd.DataFrame(ticker_data)

st.subheader("Stock Data with Last Matched Price or Higher Before Latest Date")
st.dataframe(df)

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
    st.write("No valid data available for plotting.")
