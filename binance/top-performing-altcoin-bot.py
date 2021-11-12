# https://youtu.be/g04GeHe-dJw
# thank you algovibes
# looping over general ticker to scrape top performing altcoins and then trade
# not tested

import pandas as pd
import time
from binance import Client

client = Client(api_key, api_secret)

x = pd.DataFrame(client.get_ticker())

# get all USD trades
y = x[x.symbol.str.contains('USD')]

# remove UP/DOWN tokens (leverage)
z = y[~((y.symbol.str.contains('UP')) | (y.symbol.str.contains('DOWN')))]

#z.sort_values(by='priceChangePercent', ascending=False)

# get top performing coin
z[z.priceChangePercent == z.priceChangePercent.max()]

def get_top_symbol():
    all_pairs = pd.DataFrame(client.get_ticker())
    relev = all_pairs[all_pairs.symbol.str.contains('USD')]
    non_leverage = relev[~((relev.symbol.str.contains('UP')) | (relev.symbol.str.contains('DOWN')))]
    top_symbol = non_leverage[non_leverage.priceChangePercent == non_leverage.priceChangePercent.max()]
    return top_symbol.symbol.values[0]

def getminutedata(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol, interval, loopback = ' min ago UTC'))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'High', 'Low', 'Open', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

#test
xy = getminutedata(get_top_symbol(), '1m', '120') # lookback 2 hours

def strategy(buy_amt, SL=0.98, Target=1.02, open_posiiton=False):
    try:
        asset = get_top_symbol()
        df = getminutedata(asset, '1m', '120')
    except:
        time.sleep(61)
        asset = get_top_symbol()
        df = getminutedata(asset, '1m', '120')
    # define how much assets we have to buy depending on the amount we invest
    qty = round(buy_amt/df.Close.iloc[-1])
    if ((df.Close.pct_change() + 1).cumprod()).iloc[-1] > 1:
        order = client.create_order(symbol=asset,
                    side='BUY',
                    type='MARKET',
                    quantity=qty)
        print(order)
        buyprice = float(order['fills'][0]['price'])
        open_position = True
        while open_position:
            try:
                df = getminutedata(asset, '1m', '120')
            except:
                print('Something went wrong. Script continues in 1 min')
                time.sleep(61)
                df = getminutedata(asset, '1m', '120')
            print('Current Close is ' + str(df.Close[-1]))
            print('Current Target is ' + str(buyprice * Target))
            print('Current Stop is ' + str(buyprice * SL))
            if df.Close[-1] <= buyprice * SL or df.Close[-1] >= buyprice * Target:
                order = client.create_order(symbol=asset,
                    side='SELL',
                    type='MARKET',
                    quantity=qty)
                print(order)
                break

while True:
    strategy(200)