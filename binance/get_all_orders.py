from binance import Client
import configparser
import json

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    orders = binance_client.get_all_orders(symbol='MANAUSDT', limit=10)

    print (json.dumps(orders, indent=2))