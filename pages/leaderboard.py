import os
import pandas as pd
import streamlit as st 
import threading
import warnings
import yfinance as yf 
from dotenv import load_dotenv
from src.utils import get_supabase_client, get_users


def get_portfolio_value(email):
    '''
    Given a user's email, retrieves the total principal invested in their portfolio.
    Then, calculate the current value of the portfolio.
    
    Args:
        email (str): The email of the user
    
    Returns:
        portfolio_names (list): A list of the portfolio names
        total_returns (list): A list of the total returns for each portfolio
    '''
    load_dotenv()
    STOCK_DATA_TABLE = os.environ.get("STOCK_DATA_TABLE")
    client = get_supabase_client()
    response = client.table(STOCK_DATA_TABLE).select("*").eq("owner", email).execute()
    df = pd.DataFrame.from_dict(response.data)

    if df.empty:
        return [], []

    # Only display percentage returns 
    total_returns = []
    portfolio_names = []

    # Loop through all unique portfolios
    for portfolio in df["portfolio"].unique():
        # Filter the dataframe by the current portfolio and create a copy
        portfolio_df = df[df["portfolio"] == portfolio].copy()

        # Calculate the total principal invested
        portfolio_df["total_value"] = portfolio_df["unit_price"] * portfolio_df["amount"]
        total_principal = portfolio_df["total_value"].sum()

        # Calculate the current value of the portfolio (as of prev day's close)
        current_value = 0
        for _, row in portfolio_df.iterrows():
            stock = yf.Ticker(row["stock"])
            current_value += stock.history(period="1d")["Close"].values[0] * row["amount"]
        
        # Calculate the total return as a percentage
        total_return = ((current_value - total_principal) / total_principal) * 100
        total_returns.append(total_return)
        portfolio_names.append(portfolio)
    
    return portfolio_names, total_returns


if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.switch_page("app.py")

    st.title("Leaderboard")

    # Suppress FutureWarnings due to internal yfinance implementation details
    warnings.simplefilter(action='ignore', category=FutureWarning)

    with st.spinner("Loading..."):
        # Retrieve emails and usernames from users table
        emails, usernames = get_users()

        # Multithread the retrieval of portfolio values for each user
        leaderboard = []
        threads = []
        for i, email in enumerate(emails):
            thread = threading.Thread(target=get_portfolio_value, args=(email,))
            thread.start()
            threads.append(thread)
            
            portfolio_names, total_returns = get_portfolio_value(email)
            if not portfolio_names or not total_returns:
                continue
            for j in range(len(portfolio_names)):
                total_returns[j] = "{:.2f}%".format(total_returns[j])
                leaderboard.append((usernames[i], portfolio_names[j], total_returns[j]))

        for thread in threads:
            thread.join()
        
        # Sort the leaderboard in descending order and display
        leaderboard.sort(key=lambda x: float(x[2][:-1]), reverse=True)
        df = pd.DataFrame(leaderboard, columns=["Username", "Portfolio Name", "Total Return"])
        df.index = range(1, len(df) + 1) # Index starting from 1
        st.write("Here are the top portfolios on the platform!")
        st.table(df)

    

    
    
    

