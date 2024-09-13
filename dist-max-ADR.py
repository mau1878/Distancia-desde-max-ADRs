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
        return None, None, None
    
    data.sort_index(inplace=True)
    
    # Filtrar datos para incluir entradas hasta mañana
    data_filtered = data[data.index.date <= tomorrow]
    
    if data_filtered.empty:
        return None, None, None
    
    # Encontrar la fecha más reciente disponible con un precio mayor o igual al precio de hoy
    latest_date = data_filtered.index.max().date()
    latest_price = data_filtered['Adj Close'].loc[data_filtered.index.date == latest_date].iloc[-1]
    
    # Encontrar el último precio disponible antes de la fecha más reciente
    data_before_latest = data[data.index.date < latest_date]
    
    if not data_before_latest.empty:
        data_before_latest = data_before_latest[data_before_latest['Adj Close'] >= latest_price]
        if not data_before_latest.empty:
            last_matched_date = data_before_latest.index[-1].date()
            price_at_last_matched_date = data_before_latest['Adj Close'].iloc[-1]
            return latest_price, last_matched_date, price_at_last_matched_date
        else:
            return latest_price, None, None
    else:
        return latest_price, None, None

ticker_data = []

for ticker in tickers:
    try:
        latest_price, last_date, price_at_last_date = get_latest_price(ticker)
        if latest_price is None:
            continue
        
        # Round prices to 2 decimal places
        latest_price = round(latest_price, 2)
        if price_at_last_date is not None:
            price_at_last_date = round(price_at_last_date, 2)
        
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

# Ordenar la tabla por 'Días Desde' en orden descendente
df_sorted = df.sort_values(by='Días Desde', ascending=False)

st.subheader("Datos de Acciones con Último Precio Coincidente o Superior Antes de la Fecha Más Reciente")
st.dataframe(df_sorted)

# Agregar un texto de marca de agua en la tabla
st.markdown("**MTaurus - X: MTaurus_ok**", unsafe_allow_html=True)

if 'Días Desde' in df_sorted.columns:
    df_valid = df_sorted.dropna(subset=['Días Desde'])
else:
    df_valid = df_sorted

if not df_valid.empty:
    st.subheader("Tiempo Transcurrido Desde la Última Coincidencia de Precio o Superior (en días)")
    # Ordenar las barras por longitud (en orden descendente)
    fig = px.bar(df_valid, x='Días Desde', y='Ticker', orientation='h', color='Días Desde',
                 color_continuous_scale='Viridis', labels={'Días Desde': 'Días Desde Última Coincidencia de Precio'},
                 title="Días Desde la Última Coincidencia de Precio o Superior")
    
    # Agregar marca de agua al gráfico
    fig.update_layout(yaxis_title='Ticker', xaxis_title='Días Desde', yaxis_categoryorder='total ascending')
    fig.update_traces(marker=dict(line=dict(width=1, color='rgba(0,0,0,0.2)')))
    
    fig.add_annotation(
        text="MTaurus - X: MTaurus_ok",
        xref="paper", yref="paper",
        x=0.5, y=-0.1,
        showarrow=False,
        font=dict(size=10, color="rgba(0,0,0,0.5)"),
        align="center"
    )
    
    st.plotly_chart(fig)
else:
    st.write("No hay datos válidos disponibles para graficar.")
