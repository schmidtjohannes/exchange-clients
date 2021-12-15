from binance import Client
import configparser
import pandas as pd
import ta
import time
from datetime import datetime
import math
import sys

INTERVAL_IN_MIN = 1
INTERVAL_IN_MIN_BNC_UNIT = Client.KLINE_INTERVAL_1MINUTE
SLEEP_INTERVAL_IN_SEC = 30

DOTBNB_COIN = {
  "bot_pair": "DOTBNB",
  "quantity": 2,
  "asset": "DOT",
  "float_lot": True
}

# Non altcoin
ENJBNB_COIN = {
  "bot_pair": "ENJBNB",
  "quantity": 12,
  "asset": "ENJ",
  "float_lot": False
}
# Non altcoin
FLOWBNB_COIN = {
  "bot_pair": "FLOWBNB",
  "quantity": 4,
  "asset": "FLOW",
  "float_lot": True
}

IOTABNB_COIN = {
  "bot_pair": "IOTABNB",
  "quantity": 30,
  "asset": "IOTA",
  "float_lot": False
}

SANDBNB_COIN = {
  "bot_pair": "SANDBNB",
  "quantity": 6,
  "asset": "SAND",
  "float_lot": False
}

MATICBNB_COIN = {
  "bot_pair": "MATICBNB",
  "quantity": 150,
  "asset": "MATIC",
  "float_lot": False
}

GALABNB_COIN = {
  "bot_pair": "GALABNB",
  "quantity": 280,
  "asset": "GALA",
  "float_lot": False
}

AVAILABLE_COINS = { 
    "DOT" : DOTBNB_COIN,
    "ENJ" : ENJBNB_COIN ,
    "FLOW" : FLOWBNB_COIN ,
    "IOTA" : IOTABNB_COIN ,
    "SAND" : SANDBNB_COIN  ,
    "MATIC" : MATICBNB_COIN ,
    "GALA" : GALABNB_COIN
}

COIN = {}


def add_stats(ohlc):
    indicator_bb = ta.volatility.BollingerBands(
                                ohlc.Close,
                                window=21,
                                window_dev=2)
    ohlc['bbands_upper'] = indicator_bb.bollinger_hband()
    ohlc['bbands_middle'] = indicator_bb.bollinger_mavg()
    ohlc['bbands_lower'] = indicator_bb.bollinger_lband()
    # drop NaN rows
    ohlc.dropna(inplace=True)

def get_ohlc_data(coin):
    try:
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, INTERVAL_IN_MIN_BNC_UNIT, "100 min ago"))
    except:
        time.sleep(5)
        frame = pd.DataFrame(binance_client.get_historical_klines(coin, INTERVAL_IN_MIN_BNC_UNIT, "100 min ago"))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'High', 'Low', 'Open', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

def get_time():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def create_order(coin, quantity, side='BUY'):
    print('create '+ side +' order via API')
    order = binance_client.create_order(symbol=coin,
        side=side,
        type='MARKET',
        quantity=quantity)
    order['transactTime'] = time.time()
    order['price'] = float(order['fills'][0]['price'])
    return order

def main(coin, qty, stoploss, takeprofit):
    open_position = False
    while True:
        print('\nCheck BUY at ' + get_time())
        ohlc = get_ohlc_data(coin)
        add_stats(ohlc)

        current_close = ohlc.Close.iloc[-1]
        middle = ohlc['bbands_middle'].iloc[-1]

        print('current_close ' + str(current_close))
        if not open_position and (
                current_close < middle):
            create_order(coin, qty, side='BUY')
            open_position = True
            time.sleep(SLEEP_INTERVAL_IN_SEC)
        if open_position:
            while True:
                print('\nCheck SELL at ' + get_time())

                ohlc = get_ohlc_data(coin)
                add_stats(ohlc)
                current_high = ohlc.High.iloc[-1]
                current_close = ohlc.Close.iloc[-1]
                upper = ohlc['bbands_upper'].iloc[-1]
                lower = ohlc['bbands_lower'].iloc[-1]
                middle = ohlc['bbands_middle'].iloc[-1]

                if current_high > upper or current_close < lower:
                    # sell all you have
                    current_quantity = float(binance_client.get_asset_balance(COIN['asset'])['free'])
                    if not COIN['float_lot']:
                        current_quantity = math.floor(current_quantity)
                    create_order(coin, current_quantity, side='SELL')
                    open_position = False
                    break
                time.sleep(SLEEP_INTERVAL_IN_SEC)
        # TODO each min
        time.sleep(SLEEP_INTERVAL_IN_SEC)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read_file(open('.binance'))
    api_key = config.get('BINANCE', 'KEY')
    api_secret = config.get('BINANCE', 'SECRET')
    binance_client = Client(api_key, api_secret)

    pd.set_option('display.precision',8)

    if len(sys.argv) != 2:
        sys.exit("[ERROR] - No coin passed, avialable coins: " + str(list(AVAILABLE_COINS.keys())))

    coin_arg = sys.argv[1]
    if not coin_arg in AVAILABLE_COINS:
        sys.exit("[ERROR] - " + coin_arg + " is not in " + str(list(AVAILABLE_COINS.keys())))

    COIN = AVAILABLE_COINS[coin_arg]
    main(COIN['bot_pair'], COIN['quantity'], 0.995, 1.01)
