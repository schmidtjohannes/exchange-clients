# Import WebSocket client library
from websocket import create_connection
import pandas as pd
import sqlalchemy
import json

bot_pair = 'ETHUSD'
#bot_pair = 'MINAUSD'

engine = sqlalchemy.create_engine('sqlite:///'+bot_pair+'stream.db')

def createframe(msg, symbole):
    d = {'symbole': symbole, 'Price': msg[0], 'Time': msg[2], 'BuySell': msg[3], 'OrderType': msg[4] }
    df = pd.DataFrame(data=d, index=[0])
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='s')
    return df

#testMsg = '[545,[["4607.48000","1.08524136","1636303673.717538","s","l",""]],"trade","ETH/USD"]'
#response_ = json.loads(testMsg)
#print(response_[1][0])

#createframe(response_[1][0], response_[3])

#exit()

# Connect to WebSocket API and subscribe to trade feed for XBT/USD and XRP/USD
ws = create_connection("wss://ws.kraken.com/")
splitat = 3
left, right = bot_pair[:splitat], bot_pair[splitat:]
ws.send('{"event":"subscribe", "subscription":{"name":"trade"}, "pair":["'+left+'/'+right+'"]}')

# Infinite loop waiting for WebSocket data
while True:
    msg = ws.recv()
    response_ = json.loads(str(msg))
    #print(response_)
    if 'event' in response_:
        #print('not interested in events')
        continue
#    if response_['event'] == 'heartbeat' or response_['event'] == 'systemStatus' or  response_['event'] == 'subscriptionStatus':
#        continue
    
    frame = createframe(response_[1][0], response_[3])
    frame.to_sql(bot_pair, engine, if_exists='append', index=False)
    print(frame)

