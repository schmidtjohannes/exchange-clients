import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd
import time
from websocket import create_connection
import json

ST = 7
LT = 25
TEST_MODE = False
kraken_ws = []
ETHUSD_COIN = {
  "bot_pair": "ETHUSD",
  "quantity": 0.01,
  "test_buprice": 4500
}

DOTUSD_COIN = {
  "bot_pair": "DOTUSD",
  "quantity": 1,
  "test_buprice": 42
}

COIN = DOTUSD_COIN

def getHistoricals(symbol, interval, LT):
    # 24 * 60 * 60 = 24 in unixtime
    # LT = long term interval
    # unixtime = time.time() - (24 * 60 * 60 * LT)
    unixtime = time.time() - (60 * interval * LT)
    df, last = k.get_ohlc_data(COIN['bot_pair'], interval=interval, since=unixtime)

    closes = pd.DataFrame(df['close'])
    closes.columns = ['Close']
    closes['ST'] = closes.Close.rolling(ST-1).sum()
    closes['LT'] = closes.Close.rolling(LT-1).sum()
    closes.dropna(inplace=True)
# returns something like this
#              Close        ST         LT
#dtime                                   
#2021-10-23  4168.93  24809.95  107089.91
#2021-10-22  3971.33  24494.07  106334.45
    # remove close column
    closes = closes.drop(columns=['Close'])

    # so let's remove last line
    closes = closes[:-1]
    # recreate index
    closes.reset_index(drop=True, inplace=True)
    return closes

def liveSMA(hist, live):
    liveST = (hist['ST'].values + live.Price.values) / ST
    liveLT = (hist['LT'].values + live.Price.values) / LT
    return liveST, liveLT

def createframe(msg, symbole):
    d = {'symbole': symbole, 'Price': msg[0], 'Time': msg[2], 'BuySell': msg[3], 'OrderType': msg[4] }
    df = pd.DataFrame(data=d, index=[0])
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='s')
    return df

def create_order(quantity, type='buy'):
    order = {}
    print('create '+ type +' order via API')
    if not TEST_MODE:
        order = k.add_standard_order(COIN['bot_pair'],
            type,
            'market',
            str(quantity),
            validate=False)
        if 'txid' not in order:
            raise Exception('no transaction ID found after order creation')
        trade_info = k.query_trades_info(order['txid'])
    else:
        trade_info = {}
        trade_info['price'] = COIN['test_buyprice']
    order['transactTime'] = time.time()
    order['price'] = trade_info['price']
    return order

def main(coin, qty, SL_limit, open_position = False):
    while True:
        msg = kraken_ws.recv()
        print('plain main')
        response_ = json.loads(str(msg))
        if 'event' in response_:
            #print('not interested in events')
            time.sleep(1)
            continue
        if response_:
            frame = createframe(response_[1][0], response_[3])
            print(frame)
            livest, livelt = liveSMA(historicals, frame)
            print('livest: ' + str(livest) + ' livelt: ' + str(livelt))
            if livest > livelt and not open_position:
                order = create_order(qty, type='buy')
                print(order)
                buyprice = float(order['fills'][0]['price'])
                open_position = True
            if open_position:
                if frame.Price[0] < buyprice * SL_limit or frame.Price[0] > buyprice * 1.02:
                    order = create_order(qty, type='sell')
                    print(order)
                    break
            time.sleep(1)

def create_kraken_ws():
    ws = create_connection("wss://ws.kraken.com/")
    splitat = 3
    left, right = COIN['bot_pair'][:splitat], COIN['bot_pair'][splitat:]
    ws.send('{"event":"subscribe", "subscription":{"name":"trade"}, "pair":["'+left+'/'+right+'"]}')
    return ws

if __name__ == '__main__':
    api = krakenex.API()
    k = KrakenAPI(api)
    api.load_key('.kraken.api.key')
    INTERVAL_IN_MIN = 15
    historicals = getHistoricals(COIN['bot_pair'], INTERVAL_IN_MIN, LT)
    kraken_ws = create_kraken_ws()
    main(COIN['bot_pair'], COIN['quantity'], 0.98)
