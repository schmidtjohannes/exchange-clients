from binance import Client
import configparser
import pandas as pd

import sys

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    orders = binance_client.get_my_trades(symbol=sys.argv[1] + 'USDT', limit=100)
    df = pd.DataFrame(orders)
    df = df.set_index('time')
    df.index = pd.to_datetime(df.index, unit='ms')

    df.drop(columns=['id','orderListId','quoteQty','commissionAsset','isBestMatch'], inplace=True)

    # time range
    df = df.loc['2021-12-02':'2021-12-02']
    
    print(df)
    # remove first row if SELL
    #df = df.tail(len(df) - 1)
    # remove last row if BUY
    #df = df.head(len(df) - 1)
    df["price"] = pd.to_numeric(df["price"], downcast="float")
    df["qty"] = pd.to_numeric(df["qty"], downcast="float")
    df["commission"] = pd.to_numeric(df["commission"], downcast="float")
    df['total'] = (df['price'] * df['qty']) - df['commission']
    print(df)

    buys = df[df["isBuyer"] == True]
    sells = df[df["isBuyer"] == False]

    print("Buys " + str(buys['total'].sum()))
    print("Sells " + str(sells['total'].sum()))

    print("Total in $ " + str(sells['total'].sum() - buys['total'].sum()))
    print("Total in % " + str((sells['total'].sum() - buys['total'].sum()) / buys['total'].sum()))
