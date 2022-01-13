from binance import Client
import configparser
import pandas as pd
import sys
import time

def get_current_close(coin):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=coin)
    except:
        time.sleep(5)
        ticker = binance_client.get_symbol_ticker(symbol=coin)
    return float(ticker['price'])

def create_order(coin, quantity, side='BUY'):
    print('create '+ side +' order via API')
    sideEffectType = "MARGIN_BUY"
    if side == "BUY":
        sideEffectType = "AUTO_REPAY"
    order = binance_client.create_margin_order(symbol=coin,
        side=side,
        type='MARKET',
        sideEffectType=sideEffectType,
        quantity=quantity)
    order['transactTime'] = time.time()
    order['price'] = float(order['fills'][0]['price'])
    return order

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    pd.set_option('display.precision',8)

    if len(sys.argv) != 2:
        sys.exit("[ERROR] - No coin passed")

    coin = sys.argv[1]
    orders = binance_client.get_margin_trades(symbol=coin + 'USDT', limit=1)

    print(orders)

    buy_price = float(orders[0]['price'])
    qty = orders[0]['qty']
    print("buy_price " + str(buy_price))

    current = get_current_close(coin + "USDT")
    print("current " + str(current))

    win_perc = current/buy_price
    print("win_perc " + str(win_perc))

    if win_perc < 0.98:
        print("won enough money, will sell")
        order = create_order(coin + 'USDT', qty, side='BUY')
    elif win_perc > 1.01:
        print("lost enough money, will sell")
        order = create_order(coin + 'USDT', qty, side='BUY')
        print(order)
    else:
        print("still waiting")