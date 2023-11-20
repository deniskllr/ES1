
import yfinance as yf
import datetime as dt
import pandas as pd
import numpy as np
from scipy.stats import norm


def buy_signal():
    start_date = dt.datetime(2000, 1, 1)
    start_dateB = dt.datetime(2000, 1, 1)
    end_date = dt.datetime.today()

    spx = yf.Ticker("SPY")
    spx_hist = spx.history(start=start_date, end=end_date)
    ust = yf.Ticker("GOVT")
    ust_hist = ust.history(start=start_dateB, end=end_date)

    df = pd.DataFrame({'close_SPX': spx_hist['Close']})
    df['close_govB'] = ust_hist['Close']
    df['Return_SPX'] = np.log(df['close_SPX'] / df['close_SPX'].shift(1))
    df['Return_govB'] = np.log(df['close_govB'] / df['close_govB'].shift(1))

    # Check if there are empty cells in "CloseB"
    if df['close_govB'].isnull().values.any():
        # Fill empty cells in "ReturnB" with 0
        df['Return_govB'].fillna(0, inplace=True)

    df.index = df.index.date 

    date_today = dt.datetime.now().date()

    # Calculate the 50-day moving average
    df['50D_MA'] = df['close_SPX'].rolling(window=50).mean()
    df['200D_MA'] = df['close_SPX'].rolling(window=200).mean()

    # Berechne die taegliche Standardabweichung ueber die letzten 50 Tage
    df['STD'] = df['close_SPX'].rolling(window=50).std()

    # Berechne die annualisierte Standardabweichung
    df['50d_STD'] = df['STD'] * np.sqrt(252)

    # Berechne das taegliche VaR auf Basis der letzten 50 returns
    df['VaR_1d'] = -df['50d_STD'] * norm.ppf(0.99) * np.sqrt(1/252)*-1
    
    if (df.at[date_today, "VaR_1d"] < 0.05 and (df.at[date_today, "200D_MA"] < df.at[date_today, "50D_MA"] or df.at[date_today, "VaR_1d"] < 0.02 or 1.3 * df.at[date_today, "close_SPX"] < df.at[date_today, "200D_MA"] )):
        return True
    else:
        return False
    