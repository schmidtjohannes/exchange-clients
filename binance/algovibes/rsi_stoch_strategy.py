# from https://youtu.be/r8pU-8l1KPU
# thanks algovibes
import yfinance as yf
import numpy as np
import ta
import pandas as pd

df = yf.download('EURUSD=X', start='2021-10-15', interval='30m')

df['%K'] = ta.momentum.stoch(df.High, df.Low, df.Close, window=14, smooth_window=3)
df['%D'] = df['%K'].rolling(3).mean()
df['rsi'] = ta.momentum.rsi(df.Close, window=14)
df['macd'] = ta.trend.macd_diff(df.Close)

df.dropna(inplace=True)


def gettrigger(df, lags, buy=True):
    dfx = pd.DataFrame()
    for i in range(1, lags+1):
        if buy:
            mask = (df['%K'].shift(i) < 20) & (df['%D'].shift(i) < 20)
        else: # sell
            mask = (df['%K'].shift(i) < 80) & (df['%D'].shift(i) < 80)
        dfx = dfx.append(mask, ignore_index=True)
    return dfx.sum(axis=0)

df['Buytrigger'] = np.where(gettrigger(df, 3), 1, 0)
df['Selltrigger'] = np.where(gettrigger(df, 3, buy=False), 1, 0)
df['Buy'] = np.where((df.Buytrigger) & (df['%K'].between(20,80)) & (df['%D'].between(20,80))
                            & (df.rsi > 50) & (df.macd > 0), 1, 0)
df['Sell'] = np.where((df.Selltrigger) & (df['%K'].between(20,80)) & (df['%D'].between(20,80))
                            & (df.rsi < 50) & (df.macd < 0), 1, 0)

Buying_dates, Selling_dates = [], []

for i in range(len(df) - 1):
    if df.Buy.iloc[i]:
        Buying_dates.append(df.iloc[i + 1].name)
        for num,j in enumerate(df.Sell[i:]):
            if j:
                Selling_dates.append(df.iloc[i + num + 1].name)
                break

cutit = len(Buying_dates) - len(Selling_dates)

if cutit:
    Buying_dates = Buying_dates[:-cutit]

frame = pd.DataFrame({'Buying_dates' : Buying_dates, 'Selling_dates' : Selling_dates})
print(frame)