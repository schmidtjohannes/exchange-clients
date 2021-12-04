# https://youtu.be/rYfe9Bg2GcY
# thanks to algovibes

import yfinance as yf
import pandas as pd
import ta
import numpy as np

def getactuals(df):
    Buying_dates, Selling_dates = [], []

    for i in range(len(df) - 11):
        if df.Signal.iloc[i]:
            Buying_dates.append(df.iloc[i+1].name)
            for j in range(1,11):
                if df.RSI.iloc[i + j] > 40:
                    Selling_dates.append(df.iloc[j+i+1].name)
                    break
                elif j == 10:
                    Selling_dates.append(df.iloc[j+i+1].name)

    frame = pd.DataFrame({'Buying_dates' : Buying_dates, 'Selling_dates' : Selling_dates})

    actuals = frame[frame.Buying_dates > frame.Selling_dates.shift(1)]

    actuals = frame[:1].append(actuals)
    return actuals

def tacalc(df):
    df['SMA200'] = ta.trend.sma_indicator(df.Close, window=200)
    df['RSI'] = ta.momentum.rsi(df.Close, window=10)
    df['Signal'] = np.where((df.Close > df.SMA200) & (df.RSI < 30), True, False)


df = yf.download('^GSPC', start='1996-01-01')
tacalc(df)
actualtrades = getactuals(df)

profits = \
    df.loc[actualtrades.Selling_dates].Open.values - df.loc[actualtrades.Buying_dates].Open.values

amount_profits = len(profits)
print(amount_profits)

amount_wins = len([i for i in profits if i > 0])
print(amount_wins)

print("win rate: " + str(amount_wins/amount_profits))

rel_profits = \
    (df.loc[actualtrades.Selling_dates].Open.values - df.loc[actualtrades.Buying_dates].Open.values) / df.loc[actualtrades.Buying_dates].Open.values

print("overall profit in % " + str(rel_profits.mean()))

rel_profits = (rel_profits + 1).cumprod()

print("overall profit in % " + str(rel_profits.mean()))