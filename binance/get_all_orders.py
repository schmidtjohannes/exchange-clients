from binance import Client
import configparser
import pandas as pd

import sys

def calcTotal(row):
    if row.isBuyer:
        return (row['price'] * row['qty']) - (row['commission'] * row['price'])
    else:
        return (row['price'] * row['qty']) - row['commission']


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
    df = df.loc['2021-12-03 00:00':'2021-12-04']
    print(df)
    # remove first row if SELL
    if not df.iloc[0].isBuyer:
        df = df.tail(len(df) - 1)
    #df = df.tail(len(df) - 1)
    # remove last row if BUY
    if df.iloc[-1].isBuyer:
        df = df.head(len(df) - 1)
    print(df)
    df["price"] = pd.to_numeric(df["price"], downcast="float")
    df["qty"] = pd.to_numeric(df["qty"], downcast="float")
    df["commission"] = pd.to_numeric(df["commission"], downcast="float")
    #df['total'] = (df['price'] * df['qty']) - df['commission']
    df['total'] = df.apply(calcTotal, axis=1)

    buys = df[df["isBuyer"] == True]
    sells = df[df["isBuyer"] == False]

    print("Buys " + str(buys['total'].sum()))
    print("Sells " + str(sells['total'].sum()))

    print("Total in $ " + str(sells['total'].sum() - buys['total'].sum()))
    print("Total in % " + str((sells['total'].sum() - buys['total'].sum()) / buys['total'].sum()))
    #print("Total in % " + str((sells['total'].sum() - buys['total'].sum()) / buys['total'].sum()))
    #profit = sells.total.values - buys.total.values
    #print("overall profit " + str(profit.sum()))
    #rel_profit = (sells.total.values - buys.total.values) / buys.total.values
    #print("overall profit in % " + str(rel_profit.mean()))