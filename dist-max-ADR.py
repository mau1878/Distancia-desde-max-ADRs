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
  try:
      today = datetime.now().date()
      tomorrow = today + timedelta(days=1)
      
      end_date = tomorrow.strftime('%Y-%m-%d')
      data = fetch_data(ticker, end_date)
      
      if data.empty:
          return None, None, None
      
      # Convert index to datetime if not already
      data.index = pd.to_datetime(data.index)
      
      # Get the latest date's data
      latest_date = data.index.max()
      latest_row = data.loc[latest_date]
      latest_price = latest_row['Adj Close']
      
      # Get data before the latest date
      mask = (data.index < latest_date)
      previous_data = data.loc[mask]
      
      if not previous_data.empty:
          # Find dates where price was greater than or equal to latest price
          price_matches = previous_data[previous_data['Adj Close'] >= latest_price]
          
          if not price_matches.empty:
              last_match_date = price_matches.index[-1].date()
              price_at_last_match = price_matches['Adj Close'].iloc[-1]
              return float(latest_price), last_match_date, float(price_at_last_match)
      
      return float(latest_price), None, None
      
  except Exception as e:
      st.error(f"Error processing {ticker}: {str(e)}")
      return None, None, None

# Update the main loop as well
progress_bar = st.progress(0)
ticker_data = []

for i, ticker in enumerate(tickers):
  latest_price, last_date, price_at_last_date = get_latest_price(ticker)
  
  if latest_price is not None:
      data_dict = {
          'Ticker': ticker,
          'Último Precio': round(latest_price, 2),
          'Última Fecha': last_date if last_date else 'No se encontró coincidencia',
          'Precio en Última Fecha': round(price_at_last_date, 2) if price_at_last_date else 'N/A',
          'Días Desde': (datetime.now().date() - last_date).days if last_date else None
      }
      ticker_data.append(data_dict)
  
  # Update progress bar
  progress_bar.progress((i + 1) / len(tickers))

# Create DataFrame and display
df = pd.DataFrame(ticker_data)

if df.empty:
  st.warning("No se encontraron datos para ningún ticker.")
else:
  # Sort the DataFrame if possible
  if 'Días Desde' in df.columns and df['Días Desde'].notna().any():
      df_sorted = df.sort_values(by='Días Desde', ascending=False)
  else:
      df_sorted = df

  st.subheader("Datos de Acciones con Último Precio Coincidente o Superior Antes de la Fecha Más Reciente")
  st.dataframe(df_sorted)

  # Rest of the visualization code...

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
