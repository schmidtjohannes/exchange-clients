# not working
# signal points are weird
import matplotlib.pyplot as plt
import krakenex
from pykrakenapi import KrakenAPI
import datetime
import time

if __name__ == '__main__':
    api = krakenex.API()
    k = KrakenAPI(api)

def MACD(df):
    for i in [5,13]:
        sma = 'EMA{}'.format(i)
        df[sma] = df.close.ewm(span=i).mean()

    df['MACD'] = df['EMA13'] - df['EMA5']
    df['signal'] = df.MACD.ewm(span=9).mean()
    print('indicators added')

minusFiveHours = datetime.datetime.now() - datetime.timedelta(hours = 8)
unixtime = str(int(time.mktime(minusFiveHours.timetuple())))

ohlc, last = k.get_ohlc_data("ETHUSD", interval=5, since=unixtime)

MACD(ohlc)

Buy, Sell = [], []

for i in range(2, len(ohlc)):
    if ohlc.MACD.iloc[i] > ohlc.signal.iloc[i] and ohlc.MACD.iloc[i-1] < ohlc.signal.iloc[i-1]:
        Buy.append(i)
    elif ohlc.MACD.iloc[i] < ohlc.signal.iloc[i] and ohlc.MACD.iloc[i-1] > ohlc.signal.iloc[i-1]:
        Sell.append(i)


Realbuys = [i+1 for i in Buy]
Realsells = [i+1 for i in Sell]

Buyprices = ohlc.open.iloc[Realbuys]
Sellprices = ohlc.open.iloc[Realsells]

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

plt.figure(figsize=(12,4))
plt.scatter(ohlc.iloc[Buy].index, ohlc.iloc[Buy].close, marker="^", color='green')
plt.scatter(ohlc.iloc[Sell].index, ohlc.iloc[Sell].close, marker="v", color='red')
plt.plot(ohlc.close, label='ETH Close', color='k')
plt.legend()
plt.show()
