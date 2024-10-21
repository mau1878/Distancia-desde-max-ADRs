import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

# Lista de tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS', 'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

st.title("Datos de Acciones con Precios Más Recientes")

@st.cache_data
def fetch_data(ticker, end_date):
    try:
        stock_data = yf.download(ticker, start="1900-01-01", end=end_date)
        if stock_data.empty:
            st.warning(f"No se encontraron datos para {ticker}.")
            return pd.DataFrame()
        return stock_data
    except Exception as e:
        st.error(f"Error al obtener datos para {ticker}: {e}")
        return pd.DataFrame()

def get_latest_price(ticker):
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    end_date = tomorrow.strftime('%Y-%m-%d')
    data = fetch_data(ticker, end_date)

    if data.empty:
        st.warning(f"No hay datos para {ticker}.")
        return None, pd.NaT, np.nan

    data = data.sort_index()

    # Filtrar datos hasta la fecha más reciente
    data_filtered = data[data.index.date <= today]

    if data_filtered.empty:
        st.warning(f"No hay datos filtrados para {ticker}.")
        return None, pd.NaT, np.nan

    # Última fecha con precio disponible
    latest_date = data_filtered.index.max().date()
    latest_price = data_filtered['Adj Close'].loc[data_filtered.index.date == latest_date].iloc[-1]

    if pd.isna(latest_price):
        st.warning(f"No se encontró 'Adj Close' para {ticker} en {latest_date}.")
        return None, pd.NaT, np.nan

    # Datos anteriores a la última fecha
    data_before_latest = data_filtered[data_filtered.index.date < latest_date]

    if data_before_latest.empty:
        st.warning(f"{ticker} - No hay fechas previas con precios disponibles.")
        return latest_price, pd.NaT, np.nan

    # Seleccionar la fecha anterior con precio mayor o igual al precio más reciente
    # Evitar el error 'truth value of a series is ambiguous' usando .loc[]
    matched_data = data_before_latest.loc[data_before_latest['Adj Close'] >= latest_price]

    if matched_data.empty:
        st.warning(f"{ticker} - No hay fechas previas con precio mayor o igual al último precio.")
        return latest_price, pd.NaT, np.nan

    # Seleccionar la última fecha que cumple la condición
    last_matched_index = matched_data.index.max()
    last_matched_date = last_matched_index.date()
    price_at_last_matched_date = matched_data['Adj Close'].loc[last_matched_index]

    st.info(f"{ticker} - Último Precio: {latest_price} ({latest_date}), Precio anterior igual o mayor: {price_at_last_matched_date} ({last_matched_date})")

    return latest_price, last_matched_date, price_at_last_matched_date

# Procesar datos para todos los tickers
ticker_data = []
for ticker in tickers:
    try:
        latest_price, last_date, price_at_last_date = get_latest_price(ticker)
        if latest_price is None:
            continue

        # Redondear precios a 2 decimales
        latest_price = round(latest_price, 2)
        price_at_last_date = round(price_at_last_date, 2)

        days_since = (datetime.now().date() - last_date).days if pd.notna(last_date) else np.nan

        ticker_data.append({
            'Ticker': ticker,
            'Último Precio': latest_price,
            'Última Fecha': last_date,
            'Precio en Última Fecha': price_at_last_date,
            'Días Desde': days_since
        })
    except Exception as e:
        st.error(f"Error al procesar datos para {ticker}: {e}")

# Crear DataFrame
if ticker_data:  # Check if ticker_data is not empty
    df = pd.DataFrame(ticker_data)

    # Convertir columnas a tipos adecuados
    df['Ticker'] = df['Ticker'].astype(str)
    df['Último Precio'] = pd.to_numeric(df['Último Precio'], errors='coerce')
    df['Última Fecha'] = pd.to_datetime(df['Última Fecha'], errors='coerce')
    df['Precio en Última Fecha'] = pd.to_numeric(df['Precio en Última Fecha'], errors='coerce')
    df['Días Desde'] = pd.to_numeric(df['Días Desde'], errors='coerce')

    # Ordenar la tabla
    df_sorted = df.sort_values(by='Días Desde', ascending=False, na_position='last').reset_index(drop=True)

    # Mostrar la tabla
    st.subheader("Datos de Acciones con Último Precio Coincidente o Superior Antes de la Fecha Más Reciente")
    st.dataframe(df_sorted)

    # Gráfico interactivo
    if not df_sorted.empty:
        st.subheader("Tiempo Transcurrido Desde la Última Coincidencia de Precio o Superior (en días)")
        fig = px.bar(
            df_sorted, 
            x='Días Desde', 
            y='Ticker', 
            orientation='h', 
            color='Días Desde',
            color_continuous_scale='Viridis',
            title="Días Desde la Última Coincidencia de Precio o Superior"
        )
        st.plotly_chart(fig)
    else:
        st.write("No hay datos válidos disponibles para graficar.")
else:
    st.write("No se encontraron datos válidos para procesar.")
