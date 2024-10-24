# Install required libraries (if not already installed)
# !pip install requests pandas yfinance streamlit

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime
import streamlit as st

# Define the headers for the stockanalysis request
headers = {
    'accept': '*/*',
    'accept-language': 'de-DE,de;q=0.9,es-AR;q=0.8,es;q=0.7,en-DE;q=0.6,en;q=0.5,en-US;q=0.4',
    'dnt': '1',
    'origin': 'https://stockanalysis.com',
    'priority': 'u=1, i',
    'referer': 'https://stockanalysis.com/',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
}

# List of tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS', 'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

# Data structure to store results
results = []

# Function to find the most recent date in StockAnalysis where the adjusted close is >= YFinance price
def get_closest_stockanalysis_data(ticker, latest_price):
    params = {'range': '10Y', 'period': 'Daily'}
    response = requests.get(f'https://api.stockanalysis.com/api/symbol/s/{ticker}/history', params=params, headers=headers)
    
    if response.status_code == 200:
        history_data = response.json().get('data', {}).get('data', [])
        if history_data and isinstance(history_data, list):
            df_history = pd.DataFrame(history_data)
            # Ensure the 'date' column is in datetime format
            df_history['date'] = pd.to_datetime(df_history['t'])
            df_history['adjClose'] = pd.to_numeric(df_history['a'], errors='coerce')
            
            # Filter to find rows where adjClose >= latest_price
            filtered_df = df_history[df_history['a'] >= latest_price]
            if not filtered_df.empty:
                # Get the most recent date and its price
                closest_row = filtered_df.iloc[-1]
                closest_date = closest_row['date']
                previous_price = closest_row['a']
                return closest_date, previous_price
    return None, None

# Iterate over each ticker
for ticker in tickers:
    # Fetch the latest price from YFinance
    stock = yf.Ticker(ticker)
    stock_data = stock.history(period="1d")  # Get the latest day's price
    if not stock_data.empty:
        latest_price = stock_data['Close'].values[0]
        latest_date = stock_data.index[0].date()
        
        # Find the most recent date in StockAnalysis where adjClose >= latest_price
        closest_date, previous_price = get_closest_stockanalysis_data(ticker, latest_price)
        
        if closest_date:
            # Calculate the number of days between the two dates
            days_difference = (latest_date - closest_date.date()).days
            
            # Append data to results
            results.append({
                'Ticker': ticker,
                'Latest Price (YFinance)': f"{latest_price:.2f}",
                'YFinance Date': latest_date,
                'Previous Price (StockAnalysis)': f"{previous_price:.2f}",
                'StockAnalysis Date': closest_date.date(),
                'Days Difference': days_difference
            })
        else:
            results.append({
                'Ticker': ticker,
                'Latest Price (YFinance)': f"{latest_price:.2f}",
                'YFinance Date': latest_date,
                'Previous Price (StockAnalysis)': 'N/A',
                'StockAnalysis Date': 'N/A',
                'Days Difference': 'N/A'
            })

# Convert the results into a DataFrame
df_results = pd.DataFrame(results)

# Stylish display using Streamlit
st.title("Stock Price Comparison (YFinance vs StockAnalysis)")
st.table(df_results.style.set_properties(**{
    'background-color': '#f4f4f4',
    'border-color': 'black',
    'color': 'black',
    'font-size': '12px',
    'text-align': 'center',
}).set_caption('Comparison of latest stock prices from YFinance and the closest available prices from StockAnalysis.'))
