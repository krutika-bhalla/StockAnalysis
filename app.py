import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Helper function to validate user input
def validate_input(user_input, input_type, validation_fn=None):
    """Reusable input validation function."""
    try:
        if input_type == 'date':
            user_input = datetime.strptime(user_input, '%Y-%m-%d')
        elif input_type == 'float':
            user_input = float(user_input)
        elif input_type == 'int':
            user_input = int(user_input)

        if validation_fn and not validation_fn(user_input):
            raise ValueError()
        return user_input
    except (ValueError, TypeError):
        st.error("Invalid input. Please try again.")
        return None

# Function to analyze breakouts
def analyze_breakouts(ticker, start_date, end_date, volume_threshold, price_threshold, holding_period):
    buffer_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=40)).strftime('%Y-%m-%d')
    stock = yf.download(ticker, start=buffer_start, end=end_date)
    stock = stock.droplevel('Ticker', axis=1)

    stock = stock.copy()
    stock['Daily_Return'] = stock['Close'].pct_change()
    stock['MA20_Volume'] = stock['Volume'].rolling(window=20).mean()
    stock['Volume_Ratio'] = stock['Volume'].div(stock['MA20_Volume'])

    breakouts = stock[(stock.index >= start_date) & (stock['Volume_Ratio'] > volume_threshold) & (stock['Daily_Return'] > price_threshold)]
    results = []

    for date in breakouts.index:
        entry_price = stock.loc[date, 'Close']
        future_idx = min(stock.index.get_loc(date) + holding_period, len(stock.index) - 1)
        future_date = stock.index[future_idx]
        exit_price = stock.loc[future_date, 'Close']
        forward_return = (exit_price - entry_price) / entry_price

        results.append({
            'Entry_Date': date.strftime('%Y-%m-%d'),
            'Entry_Price': round(entry_price, 2),
            'Exit_Date': future_date.strftime('%Y-%m-%d'),
            'Exit_Price': round(exit_price, 2),
            'Volume': int(stock.loc[date, 'Volume']),
            'Volume_Ratio': round(stock.loc[date, 'Volume_Ratio'], 2),
            'Daily_Return': f"{stock.loc[date, 'Daily_Return']:.1%}",
            'Forward_Return': f"{forward_return:.1%}"
        })

    if not results:
        st.error(f"No breakout signals found for {ticker} with the given parameters.")
        return None

    df = pd.DataFrame(results)
    avg_return = df['Forward_Return'].str.rstrip('%').astype(float).mean()

    st.subheader("Results")
    st.write(f"Total Signals: {len(df)}")
    st.write(f"Average Forward Return: {avg_return:.1f}%")
    st.write(f"Analysis Period: {start_date} to {end_date}")
    st.write(f"Volume Threshold: {volume_threshold * 100}%")
    st.write(f"Price Threshold: {price_threshold * 100}%")
    st.write(f"Holding Period: {holding_period} days")
    st.dataframe(df)

    csv = df.to_csv(index=False)
    if st.download_button("Download Report as CSV", csv, "breakout_analysis.csv", "text/csv"):
        st.experimental_rerun()

# Streamlit UI
def main():
    st.title("Stock Breakout Strategy Analyzer")
    
    ticker = st.text_input("Enter ticker symbol (e.g., AAPL)", "AAPL")
    start_date = st.date_input("Start date", value=datetime(2022, 1, 1))
    end_date = st.date_input("End date", value=datetime.today())
    volume_threshold = st.number_input("Volume threshold (e.g., 2 for 200%)", min_value=0.1, value=2.0)
    price_threshold = st.number_input("Price threshold (e.g., 0.02 for 2%)", min_value=0.01, max_value=1.0, value=0.02)
    holding_period = st.number_input("Holding period in days", min_value=1, value=10)

    if st.button("Run Analysis"):
        if start_date >= end_date:
            st.error("Start date must be before end date.")
        else:
            analyze_breakouts(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), volume_threshold, price_threshold, holding_period)

if __name__ == "__main__":
    main()
