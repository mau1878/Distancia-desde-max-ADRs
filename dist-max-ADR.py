import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np  # Import numpy for np.nan
from datetime import datetime, timedelta
import plotly.express as px

# Lista de tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS',
         'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

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
  
  data.sort_index(inplace=True)
  
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
  
  # Encontrar el último precio disponible antes de la fecha más reciente que sea >= latest_price
  data_before_latest = data[data.index.date < latest_date]
  
  if not data_before_latest.empty:
      matching_data = data_before_latest[data_before_latest['Adj Close'] >= latest_price]
      if not matching_data.empty:
          last_matched_index = matching_data.index[-1]
          last_matched_date = last_matched_index.date()
          price_at_last_matched_date = matching_data['Adj Close'].iloc[-1]
          price_at_last_matched_date = float(price_at_last_matched_date)  # Ensure it's a float
          st.info(f"{ticker} - Precio en Última Fecha: {price_at_last_matched_date} en {last_matched_date}")
          return latest_price, last_matched_date, price_at_last_matched_date
      else:
          st.warning(f"{ticker} - No se encontró un precio anterior >= {latest_price}.")
          return latest_price, pd.NaT, np.nan
  else:
      st.warning(f"{ticker} - No hay datos antes de {latest_date}.")
      return latest_price, pd.NaT, np.nan

ticker_data = []

for ticker in tickers:
  try:
      latest_price, last_date, price_at_last_date = get_latest_price(ticker)
      if latest_price is None:
          st.warning(f"No hay datos de precio para {ticker}.")
          continue
      
      # Round prices to 2 decimal places if they are not NaN
      latest_price = round(latest_price, 2) if not pd.isna(latest_price) else np.nan
      price_at_last_date = round(price_at_last_date, 2) if not pd.isna(price_at_last_date) else np.nan
      
      if pd.notna(last_date):
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
              'Última Fecha': pd.NaT,
              'Precio en Última Fecha': np.nan,
              'Días Desde': np.nan
          })
  except Exception as e:
      st.error(f"Error al procesar datos para {ticker}: {e}")

# Crear DataFrame
df = pd.DataFrame(ticker_data)

# Define data types explícitamente
df['Ticker'] = df['Ticker'].astype(str)
df['Último Precio'] = pd.to_numeric(df['Último Precio'], errors='coerce')
df['Última Fecha'] = pd.to_datetime(df['Última Fecha'], errors='coerce')
df['Precio en Última Fecha'] = pd.to_numeric(df['Precio en Última Fecha'], errors='coerce')
df['Días Desde'] = pd.to_numeric(df['Días Desde'], errors='coerce')

# Ordenar la tabla por 'Días Desde' en orden descendente, manejando NaN
df_sorted = df.sort_values(by='Días Desde', ascending=False, na_position='last')

# Reset the index to eliminate it from serialization
df_sorted.reset_index(drop=True, inplace=True)

# Opcional: Verificar tipos de datos
st.write("Tipos de datos del DataFrame:")
st.write(df_sorted.dtypes)

# Mostrar la tabla en Streamlit
st.subheader("Datos de Acciones con Último Precio Coincidente o Superior Antes de la Fecha Más Reciente")
st.dataframe(df_sorted)

# Agregar un texto de marca de agua en la tabla
st.markdown("**MTaurus - X: MTaurus_ok**", unsafe_allow_html=True)

# Filtrar datos válidos para graficar
df_valid = df_sorted.dropna(subset=['Días Desde'])

if not df_valid.empty:
  st.subheader("Tiempo Transcurrido Desde la Última Coincidencia de Precio o Superior (en días)")
  # Ordenar las barras por longitud (en orden descendente)
  fig = px.bar(
      df_valid, 
      x='Días Desde', 
      y='Ticker', 
      orientation='h', 
      color='Días Desde',
      color_continuous_scale='Viridis', 
      labels={'Días Desde': 'Días Desde Última Coincidencia de Precio'},
      title="Días Desde la Última Coincidencia de Precio o Superior"
  )
  
  # Agregar marca de agua al gráfico
  fig.update_layout(
      yaxis_title='Ticker', 
      xaxis_title='Días Desde', 
      yaxis_categoryorder='total ascending'
  )
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
