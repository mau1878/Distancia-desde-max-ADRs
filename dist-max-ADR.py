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
