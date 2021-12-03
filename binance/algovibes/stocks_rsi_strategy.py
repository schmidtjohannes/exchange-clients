# from https://youtu.be/pB8eJwg7LJU
# thanks algovibes
import yfinance as yf
import numpy as np
import ta
import pandas as pd
import matplotlib.pyplot as plt
pd.options.mode.chained_assignment = None


def RSIcalc(asset):
    df = yf.download(asset, start='2011-01-01')
    df['MA200'] = df['Adj Close'].rolling(window=200).mean()
    df['price change'] = df['Adj Close'].pct_change()
    df['Upmove'] = df['price change'].apply(lambda x: x if x > 0 else 0)
    df['Downmove'] = df['price change'].apply(lambda x: abs(x) if x < 0 else 0)
    df['avg Up'] = df['Upmove'].ewm(span=19).mean()
    df['avg Down'] = df['Downmove'].ewm(span=19).mean()
    df.dropna(inplace=True)
    df['RS'] = df['avg Up']/df['avg Down']
    df['RSI'] = df['RS'].apply(lambda x: 100-(100/(x+1)))
    df.loc[(df['Adj Close'] > df['MA200']) & (df['RSI'] < 30), 'Buy'] = 'Yes'
    df.loc[(df['Adj Close'] < df['MA200']) | (df['RSI'] > 30), 'Buy'] = 'No'
    return df

def getSignals(df):
    Buying_dates, Selling_dates = [], []
    for i in range(len(df)):
        if "Yes" in df['Buy'].iloc[i]:
            Buying_dates.append(df.iloc[i+1].name)
            for j in range(1,11):
                if df['RSI'].iloc[i + j] > 40:
                    Selling_dates.append(df.iloc[i+j+1].name)
                    break
                elif j == 10:
                    Selling_dates.append(df.iloc[i+j+1].name)
    return Buying_dates, Selling_dates


tickers = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
tickers = tickers.Symbol.to_list()

for i,v in enumerate(tickers):
    tickers[i] = v.replace('.','-')

frame = RSIcalc(tickers[0])
buy, sell = getSignals(frame)

# plt.figure(figsize=(12,5))
# plt.scatter(frame.loc[buy].index, frame.loc[buy]['Adj Close'], marker="^", color='g')
# plt.plot(frame['Adj Close'], alpha=0.7)
# plt.show()

Profits = (frame.loc[sell].Open.values - frame.loc[buy].Open.values) / frame.loc[buy].Open.values

print(Profits)

exit()

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