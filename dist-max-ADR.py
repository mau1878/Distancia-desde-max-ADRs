import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# Add error handling for imports
try:
  import streamlit as st
  import yfinance as yf
  import pandas as pd
  import plotly.express as px
except ImportError as e:
  st.error(f"Missing required package: {e}")
  st.stop()

# Configure page
st.set_page_config(
  page_title="Stock Price Analysis",
  page_icon="📈",
  layout="wide"
)

# Lista de tickers
tickers = ['BBAR', 'BMA', 'CEPU', 'CRESY', 'EDN', 'GGAL', 'IRS', 'LOMA', 'PAM', 'SUPV', 'TEO', 'TGS', 'YPF']

st.title("Datos de Acciones con Precios Más Recientes")

# Improved cache decorator with TTL
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_data(ticker: str, end_date: str) -> pd.DataFrame:
  """
  Fetch stock data for a given ticker
  
  Parameters:
      ticker (str): Stock ticker symbol
      end_date (str): End date for data fetch
      
  Returns:
      pd.DataFrame: Stock data
  """
  try:
      stock_data = yf.download(ticker, start="1900-01-01", end=end_date)
      
      if stock_data.empty:
          st.warning(f"No se encontraron datos para {ticker}.")
          return pd.DataFrame()
      
      return stock_data
  except Exception as e:
      st.error(f"Error al obtener datos para {ticker}: {e}")
      return pd.DataFrame()

def get_latest_price(ticker: str) -> tuple:
  """
  Get the latest price and related information for a ticker
  
  Parameters:
      ticker (str): Stock ticker symbol
      
  Returns:
      tuple: (latest_price, last_date, price_at_last_date)
  """
  today = datetime.now().date()
  tomorrow = today + timedelta(days=1)
  
  end_date = tomorrow.strftime('%Y-%m-%d')
  data = fetch_data(ticker, end_date)
  
  if data.empty:
      return None, None, None
  
  data.sort_index(inplace=True)
  data_filtered = data[data.index.date <= tomorrow]
  
  if data_filtered.empty:
      return None, None, None
  
  latest_date = data_filtered.index.max().date()
  latest_price = data_filtered['Adj Close'].loc[data_filtered.index.date == latest_date].iloc[-1]
  
  data_before_latest = data[data.index.date < latest_date]
  
  if not data_before_latest.empty:
      data_before_latest = data_before_latest[data_before_latest['Adj Close'] >= latest_price]
      if not data_before_latest.empty:
          last_matched_date = data_before_latest.index[-1].date()
          price_at_last_matched_date = data_before_latest['Adj Close'].iloc[-1]
          return latest_price, last_matched_date, price_at_last_matched_date
  
  return latest_price, None, None

# ... (previous imports and functions remain the same)

# Add progress bar
progress_bar = st.progress(0)
ticker_data = []

for i, ticker in enumerate(tickers):
  try:
      latest_price, last_date, price_at_last_date = get_latest_price(ticker)
      if latest_price is not None:
          latest_price = round(latest_price, 2)
          if price_at_last_date is not None:
              price_at_last_date = round(price_at_last_date, 2)
          
          data_dict = {
              'Ticker': ticker,
              'Último Precio': latest_price,
              'Última Fecha': last_date if last_date else 'No se encontró coincidencia',
              'Precio en Última Fecha': price_at_last_date if price_at_last_date else 'N/A',
              'Días Desde': (datetime.now().date() - last_date).days if last_date else None
          }
          ticker_data.append(data_dict)
  except Exception as e:
      st.error(f"Error al procesar datos para {ticker}: {e}")
  
  # Update progress bar
  progress_bar.progress((i + 1) / len(tickers))

# Create DataFrame and display
df = pd.DataFrame(ticker_data)

# Check if DataFrame is empty
if df.empty:
  st.warning("No se encontraron datos para ningún ticker.")
else:
  # Check if 'Días Desde' column exists and has valid data
  if 'Días Desde' in df.columns and df['Días Desde'].notna().any():
      df_sorted = df.sort_values(by='Días Desde', ascending=False)
  else:
      df_sorted = df  # Use unsorted DataFrame if no valid sorting column

  st.subheader("Datos de Acciones con Último Precio Coincidente o Superior Antes de la Fecha Más Reciente")
  st.dataframe(df_sorted)

  # Add watermark with CSS styling
  st.markdown(
      """
      <div style='text-align: center; color: rgba(0,0,0,0.5); padding: 10px;'>
          <strong>MTaurus - X: MTaurus_ok</strong>
      </div>
      """, 
      unsafe_allow_html=True
  )

  # Create visualization only if we have valid data
  if 'Días Desde' in df_sorted.columns:
      df_valid = df_sorted.dropna(subset=['Días Desde'])
      if not df_valid.empty:
          st.subheader("Tiempo Transcurrido Desde la Última Coincidencia de Precio o Superior (en días)")
          
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
          
          fig.update_layout(
              yaxis_title='Ticker',
              xaxis_title='Días Desde',
              yaxis_categoryorder='total ascending',
              margin=dict(t=50, l=0, r=0, b=50)
          )
          
          fig.update_traces(marker=dict(line=dict(width=1, color='rgba(0,0,0,0.2)')))
          
          fig.add_annotation(
              text="MTaurus - X: MTaurus_ok",
              xref="paper",
              yref="paper",
              x=0.5,
              y=-0.15,
              showarrow=False,
              font=dict(size=10, color="rgba(0,0,0,0.5)"),
              align="center"
          )
          
          st.plotly_chart(fig, use_container_width=True)
      else:
          st.warning("No hay datos válidos disponibles para graficar.")
  else:
      st.warning("No se encontró la columna 'Días Desde' en los datos.")
