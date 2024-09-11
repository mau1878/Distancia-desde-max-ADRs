import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Lista de tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS', 'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

st.title("Datos de Acciones con Precios Más Recientes")

@st.cache_data
def fetch_data(ticker, end_date):
    try:
        # Se oculta la información de depuración para el usuario
        # st.write(f"Fetching data for {ticker}...")
        stock_data = yf.download(ticker, start="1900-01-01", end=end_date)
        
        if stock_data.empty:
            st.warning(f"No se encontraron datos para {ticker}.")
            return pd.DataFrame()
        
        # st.write(f"Data for {ticker} retrieved successfully.")
        # st.write(f"Data range for {ticker}: {stock_data.index.min()} to {stock_data.index.max()}")
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
        return None, None, None
    
    data.sort_index(inplace=True)
    
    # Filtrar datos para incluir entradas hasta mañana
    data_filtered = data[data.index.date <= tomorrow]
    
    if data_filtered.empty:
        return None, None, None
    
    # Encontrar la fecha más reciente disponible con un precio mayor o igual al precio de hoy
    latest_date = data_filtered.index.max().date()
    latest_price = data_filtered['Adj Close'].loc[data_filtered.index.date == latest_date].iloc[-1]
    
    # st.write(f"Most recent date for {ticker}: {latest_date}")
    # st.write(f"Latest price for {ticker}: {latest_price}")
    
    # Encontrar el último precio disponible antes de la fecha más reciente
    data_before_latest = data[data.index.date < latest_date]
    
    if not data_before_latest.empty:
        data_before_latest = data_before_latest[data_before_latest['Adj Close'] >= latest_price]
        if not data_before_latest.empty:
            last_matched_date = data_before_latest.index[-1].date()
            price_at_last_matched_date = data_before_latest['Adj Close'].iloc[-1]
            # st.write(f"Last matched date: {last_matched_date}, Price at last matched date: {price_at_last_matched_date}")
            return latest_price, last_matched_date, price_at_last_matched_date
        else:
            return latest_price, None, None
    else:
        return latest_price, None, None

ticker_data = []

for ticker in tickers:
    st.write(f"Procesando ticker: {ticker}")
    try:
        latest_price, last_date, price_at_last_date = get_latest_price(ticker)
        if latest_price is None:
            st.write(f"No se encontraron datos para {ticker}.")
            continue
        
        if last_date:
            days_since = (datetime.now().date() - last_date).days
            ticker_data.append({
                'Ticker': ticker,
                'Último Precio': latest_price,
                'Última Fecha': last_date,
                'Precio en Última Fecha': price_at_last_date,
                'Días Desde': days_since
            })
        else:
            ticker_data.append({
                'Ticker': ticker,
                'Último Precio': latest_price,
                'Última Fecha': 'No se encontró coincidencia',
                'Precio en Última Fecha': 'N/A',
                'Días Desde': None
            })
    except Exception as e:
        st.error(f"Error al procesar datos para {ticker}: {e}")

df = pd.DataFrame(ticker_data)

st.subheader("Datos de Acciones con Último Precio Coincidente o Superior Antes de la Fecha Más Reciente")
st.dataframe(df)

if 'Días Desde' in df.columns:
    df_valid = df.dropna(subset=['Días Desde'])
else:
    df_valid = df

if not df_valid.empty:
    st.subheader("Tiempo Transcurrido Desde la Última Coincidencia de Precio o Superior (en días)")
    fig = px.bar(df_valid, x='Días Desde', y='Ticker', orientation='h', color='Días Desde',
                 color_continuous_scale='Viridis', labels={'Días Desde': 'Días Desde Última Coincidencia de Precio'})
    st.plotly_chart(fig)
else:
    st.write("No hay datos válidos disponibles para graficar.")
