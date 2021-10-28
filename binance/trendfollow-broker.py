# https://youtu.be/rc_Y6rdBqXM
# not tested
import pandas as pd
import sqlalchemy
from binance.client import client

client = Client(api_key, api_secret)

engine = sqlalchemy.create_engine('sqllite:///BTCUSDTstream.db')

df = pd.read_sql('BTCUSDT', engine)

# df.Price.plot()

#TredFollow strategy implementation
def strategy(entry, lookback, qty, open_position=False):
    while True:
        # get live data
        df = pd.read_sql('BTCUSDT', engine)
        lookbackperiod = df.iloc[-lookback:]
        cumret = (lookbackperiod.Price.pct_change() +1).cumprod() -1
        if not open_position:
            if cumret[cumret.last_valid_index()] > entry:
                order = client.create_order(symbol='BTCUSDT',
                                            side='BUY',
                                            type='MARKET',
                                            quantity=qty)
                print(order)
                open_position = True
                break
        if open_position:
            while True:
                df = pd.read_sql('BTCUSDT', engine)
                sincebuy = df.loc[df.Time > pd.to_datetime(order['transactTime'], unit='ms')]
                if len(sincebuy) > 1:
                    sincebuyret = (sincebuy.Price.pct_change() +1).cumprod() -1
                    last_entry = sincebuyret[sincebuyret.last_valid_index()]
                    if last_entry > 0.0015 or last_entry < 0.0015:
                        order = client.create_order(symbol='BTCUSDT',
                                                    side='SELL',
                                                    type='MARKET',
                                                    quantity=qty)
                        print(order)
                        break

strategy(0.001, 60, 0.001)
