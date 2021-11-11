# Import WebSocket client library
import websocket
import _thread
import pandas as pd
import sqlalchemy
import json
import time
import krakenex
from pykrakenapi import KrakenAPI

# https://support.kraken.com/hc/en-us/articles/360043283472-Python-WebSocket-recommended-Python-library-and-usage-examples

if __name__ == '__main__':
    api = krakenex.API()
    api.load_key('.kraken.api.key')
    k = KrakenAPI(api)
    bot_pair = 'ETHUSD'
    #bot_pair = 'MINAUSD'

engine = sqlalchemy.create_engine('sqlite:///'+bot_pair+'stream.db')

def createframe(msg, symbole):
    d = {'symbole': symbole, 'Price': msg[0], 'Time': msg[2], 'BuySell': msg[3], 'OrderType': msg[4] }
    df = pd.DataFrame(data=d, index=[0])
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='s')
    return df

# Define WebSocket callback functions
def ws_message(ws, msg):
    response_ = json.loads(str(msg))
    if 'event' in response_:
        return
    frame = createframe(response_[1][0], response_[3])
    frame.to_sql(bot_pair, engine, if_exists='append', index=False)
    print(frame)

def ws_open(ws):
    splitat = 3
    left, right = bot_pair[:splitat], bot_pair[splitat:]
    ws.send('{"event":"subscribe", "subscription":{"name":"trade"}, "pair":["'+left+'/'+right+'"]}')

def ws_thread(*args):
    ws = websocket.WebSocketApp("wss://ws.kraken.com/", on_open = ws_open, on_message = ws_message)
    ws.run_forever()

# Start a new thread for the WebSocket interface
#_thread.start_new_thread(ws_thread, ())
# todo: https://support.kraken.com/hc/en-us/articles/360044504011-WebSocket-API-unexpected-disconnections-from-market-data-feeds

#time.sleep(15)

def create_order(quantity, type='buy'):
    print('will try to create order via API')
    order = k.add_standard_order(bot_pair,
        type,
        'market',
        quantity,
        validate=False)
    if 'txid' not in order:
        raise Exception('no transaction ID found after order creation')
    print('order type:' + type)
    order['transactTime'] = time.time()
    return order

def strategy(entry, lookback, qty, open_position=False):
    while True:
        # get live data
        df = pd.read_sql(bot_pair, engine)
        print('current: ' + str(df.iloc[-1:].Price.values))
        lookbackperiod = df.iloc[-lookback:]
        cumret = (lookbackperiod.Price.pct_change() +1).cumprod() -1
        print('cumret: ' + str(cumret[cumret.last_valid_index()]))
        if not open_position:
            if cumret[cumret.last_valid_index()] > entry:
                order = create_order(qty, type='buy')
                print(order)
                open_position = True
                # now we have our open position so let's check when to sell
                continue
        if open_position:
            while True:
                df = pd.read_sql(bot_pair, engine)
                print('current: ' + str(df.iloc[-1:].Price.values))
                sincebuy = df.loc[df.Time > pd.to_datetime(order['transactTime'], unit='s')]
                if len(sincebuy) > 1:
                    sincebuyret = (sincebuy.Price.pct_change() +1).cumprod() -1
                    last_entry = sincebuyret[sincebuyret.last_valid_index()]
                    print('last_entry: ' + str(last_entry))
                    if last_entry == 0:
                        time.sleep(1)
                        continue
                    if last_entry > 0.0015 or last_entry < -0.0015:
                        order = create_order(qty, type='sell')
                        print(order)
                        open_position = False
                        break
                time.sleep(1)
            break
        time.sleep(1)

strategy(0.001, 60, 0.004)