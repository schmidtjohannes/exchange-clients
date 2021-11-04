import matplotlib.pyplot as plt
import krakenex
from pykrakenapi import KrakenAPI
import datetime
import time

if __name__ == '__main__':
    api = krakenex.API()
    k = KrakenAPI(api)

# create MA 5,8,13
def MACD(df):
    for i in [5,8,13]:
        sma = 'SMA_{}'.format(i)
        df[sma] = df.close.rolling(i, min_periods=1).mean()
        df.loc[:, sma] = df[sma].shift(-(i-1))
    # drop NaN rows
    df.drop(df.tail(12).index,inplace=True)
    print('indicators added')

minusFiveHours = datetime.datetime.now() - datetime.timedelta(hours = 8)
unixtime = str(int(time.mktime(minusFiveHours.timetuple())))

ohlc, last = k.get_ohlc_data("ETHUSD", interval=5, since=unixtime)
#print(ohlc)

MACD(ohlc)

Buy, Sell = [], []

for i in range(len(ohlc)):
    if ohlc.SMA_5.iloc[i] > ohlc.SMA_13.iloc[i] and ohlc.SMA_5.iloc[i-1] < ohlc.SMA_13.iloc[i-1]:
        Sell.append(i)
    if ohlc.SMA_5.iloc[i] < ohlc.SMA_13.iloc[i] and ohlc.SMA_5.iloc[i-1] > ohlc.SMA_13.iloc[i-1]:
        Buy.append(i)


#    if ohlc.SMA_5.iloc[i] > ohlc.SMA_8.iloc[i] and ohlc.SMA_5.iloc[i-1] < ohlc.SMA_8.iloc[i-1] \
#        and ohlc.SMA_5.iloc[i] > ohlc.SMA_13.iloc[i] and ohlc.SMA_5.iloc[i-1] < ohlc.SMA_13.iloc[i-1]:
#        Sell.append(i)
#    if ohlc.SMA_5.iloc[i] < ohlc.SMA_8.iloc[i] and ohlc.SMA_5.iloc[i-1] > ohlc.SMA_8.iloc[i-1] \
#        and ohlc.SMA_5.iloc[i] < ohlc.SMA_13.iloc[i] and ohlc.SMA_5.iloc[i-1] > ohlc.SMA_13.iloc[i-1]:
#        Buy.append(i)

print(ohlc)

plt.plot(ohlc.close, label='ETHUSD Close', color='k')
plt.plot(ohlc.SMA_5, label='SMA_5', color='green')
plt.plot(ohlc.SMA_8, label='SMA_8', color='violet')
plt.plot(ohlc.SMA_13, label='SMA_13', color='blue')
plt.scatter(ohlc.iloc[Buy].index, ohlc.iloc[Buy].close, marker="^", color='green')
plt.scatter(ohlc.iloc[Sell].index, ohlc.iloc[Sell].close, marker="v", color='red')
plt.legend()
plt.show()