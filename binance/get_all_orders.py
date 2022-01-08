#!/usr/bin/env python3

from binance import Client
import configparser
import pandas as pd
from datetime import datetime, timedelta
import sys

def calcTotal(row):
    # switch to bnb no need to distinguish commission asset
    # if row.isBuyer:
    #     return (row['price'] * row['qty']) - (row['commission'] * row['price'])
    # else:
        #return (row['price'] * row['qty']) - row['commission']
        return row['price'] * row['qty']

def calcStats(symbol, current_bnb):
   orders = binance_client.get_my_trades(symbol=symbol + 'BNB', limit=100)
   if orders == []:
      print("")
      print("no trades found for " + symbol)
      print("")
      exit()
   df = pd.DataFrame(orders)
   df = df.set_index('time')
   df.index = pd.to_datetime(df.index, unit='ms')

   #df.drop(columns=['id','orderListId','quoteQty','commissionAsset','isBestMatch'], inplace=True)
   df.drop(columns=['id','orderListId','quoteQty','isBestMatch'], inplace=True)

   today = datetime.today()
   yesterday = datetime.now() - timedelta(1)
   lookup_date_yesterday = datetime.strftime(yesterday, '%Y-%m-%d')
   lookup_date = datetime.strftime(today, '%Y-%m-%d')
   # BNB only
   df = df[df['commissionAsset'] == 'BNB']
   # time range
   # df = df.loc[lookup_date_yesterday:lookup_date]
   df = df.loc['2021-12-22 14:28':'2021-12-24']
   
   # remove first row if SELL
   # while not df.iloc[0].isBuyer:
      # df = df.tail(len(df) - 1)
   
   # remove last row if BUY
   # while df.iloc[-1].isBuyer:
      # df = df.head(len(df) - 1)
   # df = df.tail(3)
   # df = df.head(len(df) - 1)

   df["price"] = pd.to_numeric(df["price"], downcast="float")
   df["qty"] = pd.to_numeric(df["qty"], downcast="float")
   df["commission"] = pd.to_numeric(df["commission"], downcast="float")
   df['total'] = df.apply(calcTotal, axis=1)

   print(len(df))
   print(df)

   buys = df[df["isBuyer"] == True]
   sells = df[df["isBuyer"] == False]

   print("\nResults for " + symbol)
   print(str(len(buys)) + " Buys in USDT $ " + str(buys['total'].sum() * current_bnb))
   print(str(len(sells)) + " Sells in USDT $ " + str(sells['total'].sum() * current_bnb))

   print("Total in USDT $ " + str((sells['total'].sum() - buys['total'].sum()) * current_bnb))
   print("Total Commission in USDT $ " + str(df['commission'].sum() * current_bnb))
   print("Total Win minus commission in USDT $ " + str((sells['total'].sum() - buys['total'].sum() - df['commission'].sum()) * current_bnb))
   print("Total in % " + str((sells['total'].sum() - buys['total'].sum() - df['commission'].sum()) / buys['total'].sum()))
   
   # print(df.loc[sells.index].price.values)
   # print(df.loc[buys.index].price.values)
   
   # calc real profit per buy/sell pair
   # total = 0.0
   # commission = 0.0
   # profits = []
   # for i, row in df.iterrows():
   #    print("")
   #    print(str(i))
   #    print(row['isBuyer'])
   #    if not row['isBuyer']:
   #       print('continue')
   #       profits.append(total - commission)
   #       total = 0.0
   #       commission = 0.0
   #       continue
   #    total += (row['price'] * row['qty'])
   #    commission += row['commission']
   #    print(str(total))
   #    for y, yrow in (sells[sells.index > i]).iterrows():
   #       print('add sells')
   #       print(yrow['isBuyer'])
   #       if yrow['isBuyer']:
   #          total -= (yrow['price'] * yrow['qty'])
   #          commission += yrow['commission']
   #          print(str(total))
   #          break
   #    print('append')
   # print(profits)


   # rel_profits = \
   #    (df.loc[actualtrades.Selling_dates].Open.values - df.loc[actualtrades.Buying_dates].Open.values) / df.loc[actualtrades.Buying_dates].Open.values

   # print("overall profit in % " + str(rel_profits.mean()))

   # rel_profits = (rel_profits + 1).cumprod()

   # print("overall profit in % " + str(rel_profits.mean()))

if __name__ == '__main__':
   config = configparser.ConfigParser()
   config.read_file(open('.binance'))
   api_key = config.get('BINANCE', 'KEY')
   api_secret = config.get('BINANCE', 'SECRET')
   binance_client = Client(api_key, api_secret)

   pd.set_option('display.precision',8)
   # symbol = sys.argv[1]

   ticker = binance_client.get_symbol_ticker(symbol="BNBUSDT")
   current_bnb = float(ticker['price'])

   # for symbol in ['ENJ', 'DOT', 'MATIC', 'GALA', 'IOTA', 'SAND']:
   # for symbol in ['LUNA', 'ONE', 'MATIC', 'AAVE', 'NEAR']:
   for symbol in ['AAVE', 'NEAR', 'MATIC']:
      calcStats(symbol, current_bnb)