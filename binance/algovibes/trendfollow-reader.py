# https://youtu.be/rc_Y6rdBqXM
# not tested
import pandas as pd
import sqlalchemy
from binance.client import client
from binance.client import BinanceSocketManager

client = Client(api_key, api_secret)

bsm = BinanceSocketManager(client)

socket = bsm.trade_socket('BTCUSDT')

engine = sqlalchemy.create_engine('sqllite:///BTCUSDTstream.db')

def createframe(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:,['s','E','p']]
    df.columns = ['symbole', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df

while True:
    await socket.__aenter__()
    msg = await socket.recv()
    frame = createframe(msg)
    frame.to_sql('BTCUSDT', engine, if_exists='append', index=False)
    print(msg)