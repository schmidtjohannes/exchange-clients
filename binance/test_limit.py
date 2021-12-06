from binance import Client
import configparser
import time

def create_order(symbol, quantity, price, side='BUY'):
    print('create '+ side +' order via API')
    order = binance_client.order_limit(symbol=symbol,
        side=side,
        price=price,
        quantity=quantity)
    order['transactTime'] = time.time()
    #order['price'] = float(order['fills'][0]['price'])
    return order

def create_margin_order(coin, quantity, side='BUY'):
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

def get_current_close(coin):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=coin)
    except:
        time.sleep(5)
        ticker = binance_client.get_symbol_ticker(symbol=coin)
    return float(ticker['price'])

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    coin = "ETHUSDT"
    #price = get_current_close(coin)
    #print(price)
    order = create_margin_order(coin, 0.01, side='BUY')
    print(order)