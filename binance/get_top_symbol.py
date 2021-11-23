from binance import Client
import configparser
import pandas as pd
import time
import math

def get_top_symbol():
    all_pairs = pd.DataFrame(binance_client.get_ticker())
    relev = all_pairs[all_pairs.symbol.str.contains('USDT')]
    non_leverage = relev[~((relev.symbol.str.contains('UP')) | (relev.symbol.str.contains('DOWN')))]
    top_symbol = non_leverage[non_leverage.priceChangePercent == non_leverage.priceChangePercent.max()]
    return non_leverage.sort_values(by=['priceChangePercent'], ascending=False).head(10)

def create_order(coin, quantity, side='BUY', leverage=None):
    print('create '+ side +' order via API')
    order = binance_client.create_order(symbol=coin,
        side=side,
        type='MARKET',
        quantity=quantity)
    order['transactTime'] = time.time()
    if side == "BUY":
        order['price'] = float(order['fills'][0]['price'])
    return order

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    print(get_top_symbol())
    #print(binance_client.get_asset_balance("BLZ"))

    #current_quantity = float(binance_client.get_asset_balance("BLZ")['free'])
    #floorqty = math.floor(current_quantity)
    #print(create_order("BLZUSDT", floorqty, side="SELL"))