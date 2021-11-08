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
_thread.start_new_thread(ws_thread, ())
# todo: https://support.kraken.com/hc/en-us/articles/360044504011-WebSocket-API-unexpected-disconnections-from-market-data-feeds

def create_order(qunatity, type='buy'):
#    order = k.add_standard_order(pair=bot_pair,
#        ordertype='market',
#        type='buy',
#        valume=qunatity)
    print('create order: ' + type)
    d = {'transactTime': pd.to_datetime(time.now(), unit='ms') }
    df = pd.DataFrame(data=d, index=[0])
    return df

def strategy(entry, lookback, qty, open_position=False):
    while True:
        # get live data
        df = pd.read_sql(bot_pair, engine)
        lookbackperiod = df.iloc[-lookback:]
        cumret = (lookbackperiod.Price.pct_change() +1).cumprod() -1
        if not open_position:
            if cumret[cumret.last_valid_index()] > entry:
                order = create_order(qty, type='buy')
                print(order)
                open_position = True
                break
        if open_position:
            while True:
                df = pd.read_sql(bot_pair, engine)
                sincebuy = df.loc[df.Time > pd.to_datetime(order['transactTime'], unit='ms')]
                if len(sincebuy) > 1:
                    sincebuyret = (sincebuy.Price.pct_change() +1).cumprod() -1
                    last_entry = sincebuyret[sincebuyret.last_valid_index()]
                    if last_entry > 0.0015 or last_entry < 0.0015:
                        order = create_order(qty, type='sell')
                        print(order)
                        break

strategy(0.001, 60, 0.001)