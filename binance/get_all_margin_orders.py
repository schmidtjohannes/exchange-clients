#!/usr/bin/env python3

from binance import Client
import configparser
import pandas as pd
from datetime import datetime, timedelta
import sys

def calcTotal(row):
        return row['price'] * row['qty']


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    pd.set_option('display.precision',8)

    orders = binance_client.get_margin_trades(symbol=sys.argv[1] + 'USDT', limit=100)
    df = pd.DataFrame(orders)
    df = df.set_index('time')
    df.index = pd.to_datetime(df.index, unit='ms')
    
    df.drop(columns=['id','orderId','isBestMatch'], inplace=True)

    today = datetime.today()
    yesterday = yesterday = datetime.now() - timedelta(1)
    lookup_date_yesterday = datetime.strftime(yesterday, '%Y-%m-%d')
    lookup_date = datetime.strftime(today, '%Y-%m-%d')

    # BNB only
    df = df[df['commissionAsset'] == 'BNB']
    # time range
    df = df.loc[lookup_date_yesterday:lookup_date]

    # remove first row if BUY
    # while df.iloc[0].isBuyer:
        # df = df.head(len(df) - 1)
    
    # remove last row if SELL
    # while not df.iloc[-1].isBuyer:
        # df = df.tail(len(df) - 1)
    # df = df.tail(len(df) - 1)
    df = df.head(len(df) - 1)


    print(df)

    df["price"] = pd.to_numeric(df["price"], downcast="float")
    df["qty"] = pd.to_numeric(df["qty"], downcast="float")
    df["commission"] = pd.to_numeric(df["commission"], downcast="float")
    df['total'] = df.apply(calcTotal, axis=1)

    buys = df[df["isBuyer"] == True]
    sells = df[df["isBuyer"] == False]

    print(str(len(buys)) + " Buys in $ " + str(buys['total'].sum()))
    print(str(len(sells)) + " Sells in $ " + str(sells['total'].sum()))

    print("Total in $ " + str(buys['total'].sum() - sells['total'].sum()))
    print("Total Commission in $ " + str(df['commission'].sum()))
    print("Total Win minus commission in $ " + str(buys['total'].sum() - sells['total'].sum() - df['commission'].sum()))
    print("Total in % " + str((buys['total'].sum()- sells['total'].sum() - df['commission'].sum()) / sells['total'].sum()))