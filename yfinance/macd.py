# Algorithmic Trading in Python - MACD: Construction and Backtest
# https://www.youtube.com/watch?v=JzdVPnCSSuo

import yfinance as yf
import matplotlib.pyplot as plt

df = yf.download('TSLA', start='2020-11-01', end='2021-05-01')

#print(df)

def MACD(df):
    df['EMA12'] = df.Close.ewm(span=12).mean()
    df['EMA26'] = df.Close.ewm(span=26).mean()
    df['MACD'] = df['EMA26'] - df['EMA12']
    df['signal'] = df.MACD.ewm(span=9).mean()
    print('indicators added')

MACD(df)

#print(df)

#plt.plot(df.signal, label='signal', color='red')
#plt.plot(df.MACD, label='MACD', color='green')
#plt.legend()
#plt.show()

Buy, Sell = [],[]

# skipp first 2 rows because MACD/signal is still 0 here
for i in range(2, len(df)):
    if df.MACD.iloc[i] > df.signal.iloc[i] and df.MACD.iloc[i-1] < df.signal.iloc[i-1]:
        Buy.append(i)
    elif df.MACD.iloc[i] < df.signal.iloc[i] and df.MACD.iloc[i-1] > df.signal.iloc[i-1]:
        Sell.append(i)

#plt.figure(figsize=(12,4))
#plt.scatter(df.iloc[Buy].index, df.iloc[Buy].Close, marker="^", color='green')
#plt.scatter(df.iloc[Sell].index, df.iloc[Sell].Close, marker="v", color='red')
#plt.plot(df.Close, label='TESLA Close', color='k')
#plt.legend()
#plt.show()

Realbuys = [i+1 for i in Buy]
Realsells = [i+1 for i in Sell]

Buyprices = df.Open.iloc[Realbuys]
Sellprices = df.Open.iloc[Realsells]

print(Buyprices)
print(Sellprices)

if Sellprices.index[0] < Buyprices.index[0]:
    Sellprices = Sellprices.drop(Sellprices.index[0])
if Buyprices.index[0] < Sellprices.index[0]:
    Buyprices = Buyprices.drop(Buyprices.index[0])

# relative profit
profitsrel = []

for i in range(len(Sellprices)):
    profitsrel.append((Sellprices[i] - Buyprices[i]) / Buyprices[i])

print(profitsrel)