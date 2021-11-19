# from https://youtu.be/BhOdgrxWi5c
# thank you algovibes
# intraday trading strategy
# not tested

import yfinance as yf
import pandas as pd
import datetime as dt

asset = 'TSLA'

#entry = threshold of asset
#exit = how much lost/profit
def Intradaytrend(df, entry, exit):
    ret_120min = df.iloc[120].Open/df.iloc[0].Open - 1
    tick_return = df.Open.pct_change()
    if ret_120min > entry:
        buyprice = df.iloc[121].Open
        buytime = df.iloc[121].name
        cumulated = (tick_return.loc[buytime:] + 1).cumprod() - 1
        exittime = cumulated[(cumulated < -exit) | (cumulated > exit)].first_valid_index()
        if exittime == None:
            exitprice = df.iloc[-1].Open
        else:
            exitprice = df.loc[exittime + dt.timedelta(minutes=1)].Open
        profit = exitprice - buyprice
        profitrel = profit / buyprice
        return profitrel
    else:
        return None

# backtest
datesframe = yf.download(asset, start='2021-10-16', end='2021-11-15')

print(datesframe.index)
frames = []

for i in datesframe.index:
    frames.append(yf.download(asset, start=i, end= i + dt.timedelta(days=1), interval='1m'))

returns = []
for i in frames:
    returns.append(Intradaytrend(i, 0.02, 0.01))

print(pd.DataFrame(returns).mean())