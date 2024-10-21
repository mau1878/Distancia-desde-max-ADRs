import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Function to fetch data from yfinance
def fetch_data(ticker, end_date):
    return yf.download(ticker, end=end_date)

# Function to get the latest price and the previous date where the price was equal or higher than the latest
def get_latest_price(ticker):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    end_date = tomorrow.strftime('%Y-%m-%d')
    data = fetch_data(ticker, end_date)

    if data.empty:
        st.warning(f"No hay datos para {ticker}.")
        return None, pd.NaT, np.nan

    data = data.sort_index()

    # Filtrar datos para incluir entradas hasta mañana
    data_filtered = data[data.index.date <= tomorrow]

    if data_filtered.empty:
        st.warning(f"No hay datos filtrados para {ticker}.")
        return None, pd.NaT, np.nan

    # Encontrar la fecha más reciente disponible
    latest_date = data_filtered.index.max().date()
    latest_price_series = data_filtered['Adj Close'].loc[data_filtered.index.date == latest_date]

    if latest_price_series.empty:
        latest_price = None
        st.warning(f"No se encontró 'Adj Close' para {ticker} en {latest_date}.")
    else:
        latest_price = latest_price_series.iloc[-1]
        latest_price = float(latest_price)  # Ensure it's a float
        st.info(f"{ticker} - Último Precio: {latest_price} en {latest_date}")

    if latest_price is None:
        return None, pd.NaT, np.nan

    # Buscar la sesión previa donde el precio fue igual o mayor al precio más reciente
    data_before_latest = data[data.index.date < latest_date]

    if not data_before_latest.empty:
        # Encontrar la fecha más reciente previa donde el precio ajustado fue >= al más reciente
        condition = data_before_latest['Adj Close'] >= latest_price
        if condition.any():
            last_matched_index = data_before_latest[condition].index.max()

            last_matched_date = last_matched_index.date()
            price_at_last_matched_date = data_before_latest['Adj Close'].loc[last_matched_index]
            price_at_last_matched_date = float(price_at_last_matched_date)  # Ensure it's a float

            st.info(f"{ticker} - Precio igual o mayor en Fecha Previa: {price_at_last_matched_date} en {last_matched_date}")
            return latest_price, last_matched_date, price_at_last_matched_date
        else:
            st.warning(f"{ticker} - No hay fechas previas con precio igual o mayor al último precio.")
            return latest_price, pd.NaT, np.nan
    else:
        st.warning(f"{ticker} - No hay datos antes de {latest_date}.")
        return latest_price, pd.NaT, np.nan

# Main function
def main():
    st.title("Análisis de Precios de Acciones")

    # Input tickers
    tickers = st.text_input("Ingresar tickers separados por comas", "BBAR,BMA,CEPU")

    if tickers:
        ticker_list = [ticker.strip().upper() for ticker in tickers.split(",")]

        # Initialize empty DataFrame for results
        results = []

        # Loop over tickers
        for ticker in ticker_list:
            latest_price, last_matched_date, price_at_last_matched_date = get_latest_price(ticker)

            # Append results to the DataFrame
            if latest_price is not None:
                results.append([ticker, latest_price, last_matched_date, price_at_last_matched_date])

        # Convert results to DataFrame
        results_df = pd.DataFrame(results, columns=["Ticker", "Último Precio", "Última Fecha", "Precio en Última Fecha"])

        # Display results in a table
        st.write(results_df)

# Run the main function
if __name__ == "__main__":
    main()
