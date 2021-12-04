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

    coin = "MATICUSDT"
    price = get_current_close(coin)
    print(price)
    order = create_order(coin, 10, price, side='SELL')
    print(order)