from binance import Client
import configparser
import pandas as pd
import ta
import time
from datetime import datetime
import math
import sys

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    pd.set_option('display.precision',8)

    all_pairs = pd.DataFrame(binance_client.get_ticker())
    relev = all_pairs[all_pairs.symbol.str.endswith('USDT')]
    non_leverage = relev[~((relev.symbol.str.contains('UP')) | (relev.symbol.str.contains('DOWN')))]
    
    # ['symbol', 'priceChange', 'priceChangePercent', 'weightedAvgPrice',
    #    'prevClosePrice', 'lastPrice', 'lastQty', 'bidPrice', 'bidQty',
    #    'askPrice', 'askQty', 'openPrice', 'highPrice', 'lowPrice', 'volume',
    #    'quoteVolume', 'openTime', 'closeTime', 'firstId', 'lastId', 'count']
    non_leverage.drop(columns=
        ['prevClosePrice', 'lastQty', 'bidPrice', 'bidQty', 'askPrice', 'askQty', 'volume', 'weightedAvgPrice', 'priceChange',
        'openPrice', 'highPrice', 'lowPrice', 'openTime', 'closeTime', 'firstId', 'lastId', 'count']
        , inplace=True)
    # non_leverage = non_leverage.sort_values(["priceChangePercent", "volume"], ascending = (False, False))
    non_leverage["quoteVolume"] = pd.to_numeric(non_leverage["quoteVolume"], downcast="float")
    # non_leverage["volume"] = pd.to_numeric(non_leverage["volume"], downcast="float")
    non_leverage["lastPrice"] = pd.to_numeric(non_leverage["lastPrice"], downcast="float")
    non_leverage["priceChangePercent"] = pd.to_numeric(non_leverage["priceChangePercent"], downcast="float")
    non_leverage = non_leverage.loc[non_leverage['quoteVolume'] > 50000000]
    non_leverage = non_leverage.loc[non_leverage['priceChangePercent'] > 0]
    non_leverage = non_leverage.sort_values(["priceChangePercent"], ascending = (False))
    print(non_leverage)