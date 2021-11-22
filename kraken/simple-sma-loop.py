import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd
import time
from datetime import datetime
import sys
import os, psutil
import gc

INTERVAL_IN_MIN = 15
INITIAL_DELAY_IN_MIN = INTERVAL_IN_MIN

ETHUSD_COIN = {
  "bot_pair": "ETHUSD",
  "quantity": 0.01
}

DOTUSD_COIN = {
  "bot_pair": "DOTUSD",
  "quantity": 1
}
# Non altcoin
MANAUSD_COIN = {
  "bot_pair": "MANAUSD",
  "quantity": 7
}
# Non altcoin
LRCUSD_COIN = {
  "bot_pair": "LRCUSD",
  "quantity": 15
}
# Non altcoin
ENJUSD_COIN = {
  "bot_pair": "ENJUSD",
  "quantity": 2
}
# Non altcoin
FLOWUSD_COIN = {
  "bot_pair": "FLOWUSD",
  "quantity": 0.2
}

AVAILABLE_COINS = { "MANA" : MANAUSD_COIN , "DOT" : DOTUSD_COIN, "ETH" : ETHUSD_COIN , "LRC" : LRCUSD_COIN , "ENJ" : ENJUSD_COIN , "FLOW" : FLOWUSD_COIN }

COIN = {}

def print_memory():
    print("[TRACE] - Memory usage in MB: " + str(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2))
    print("")

def SMA(df):
    closes = pd.DataFrame(df['close'])
    closes.columns = ['Close']
    for i in [5,8]:
        sma = 'SMA_{}'.format(i)
        closes[sma] = closes.Close.rolling(i, min_periods=1).mean()
        closes.loc[:, sma] = closes[sma].shift(-(i-1))
    # drop NaN rows
    closes.dropna(inplace=True)
    return closes

def get_ohlc_data(coin):
    unixtime = time.time() - (60 * 60 * INTERVAL_IN_MIN)
    try:
        ohlc, last = k.get_ohlc_data(coin, interval=INTERVAL_IN_MIN, since=unixtime)
    except:
        time.sleep(5)
        ohlc, last = k.get_ohlc_data(coin, interval=INTERVAL_IN_MIN, since=unixtime)
    return ohlc

def get_time():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

def get_current_close(coin):
    try:
        ticker = k.get_ticker_information(coin)
    except:
        time.sleep(5)
        ticker = k.get_ticker_information(coin)
    return float(ticker['c'][0][0])

def create_order(quantity, type='buy', leverage=None):
    print('create '+ type +' order via API')
    order = k.add_standard_order(pair=COIN['bot_pair'], type=type, ordertype='market', volume=quantity, leverage=leverage, validate=False)
    if 'txid' not in order:
        raise Exception('no transaction ID found after order creation')
    time.sleep(1)
    txid = k.query_orders_info(order['txid'][0], trades=True).iloc[0]['trades'][0]
    trade_info = k.query_trades_info(txid)
    order['transactTime'] = time.time()
    order['price'] = float(trade_info.iloc[0]['price'])
    return order

def get_previous_sma_values(closes):
    return closes.iloc[1]['SMA_5'], closes.iloc[1]['SMA_8']

def get_current_sma_values(closes):
    return closes.iloc[0]['SMA_5'], closes.iloc[0]['SMA_8']

def main(coin, qty, stoploss, takeprofit):
    open_position = False
    while True:
        print('\nCheck BUY at ' + get_time())
        ohlc = get_ohlc_data(coin)
        buy_SMA_closes = SMA(ohlc)
        shortTerm, longTerm = get_current_sma_values(buy_SMA_closes)
        time.sleep(1)
        current_close = get_current_close(coin)
        print('current_close ' + str(current_close))
        print('shortTerm ' + str(shortTerm))
        print('longTerm ' + str(longTerm))
        print_memory()
        del ohlc
        del buy_SMA_closes
        gc.collect()
        time.sleep(5)
        if shortTerm >= longTerm and current_close >= shortTerm:
            order = create_order(qty, type='buy')
            print_memory()
            open_position = True
            time.sleep(5)
        if open_position:
            while True:
                print('\nCheck SELL at ' + get_time())
                print_memory()
                # let's wait one interval before start checking
                if order['transactTime'] + (60 * INITIAL_DELAY_IN_MIN) > time.time():
                    print('Sleep until initial INTERVAL is over')
                    time.sleep(INITIAL_DELAY_IN_MIN)
                    continue
                ohlc = get_ohlc_data(coin)
                SMA_closes = SMA(ohlc)
                print_memory()
                time.sleep(1)
                current_close = get_current_close(coin)
                print_memory()
                print('current_close ' + str(current_close))
                print('order[price] ' + str(order['price']))
                print('shortTerm ' + str(shortTerm))
                print('longTerm ' + str(longTerm))
                shortTerm, longTerm = get_previous_sma_values(SMA_closes)
                del SMA_closes
                del ohlc
                gc.collect()
                print_memory()
                if shortTerm < longTerm or current_close < order['price'] * stoploss or current_close > order['price'] * takeprofit:
                    order = create_order(qty, type='sell')
                    open_position = False
                    order = {}
                    break
                time.sleep(15)
        # TODO each min
        time.sleep(15)

if __name__ == '__main__':
    api = krakenex.API()
    k = KrakenAPI(api)
    api.load_key('.kraken.api.key')

    print_memory()
    if len(sys.argv) != 2:
        sys.exit("[ERROR] - No coin passed, avialable coins: " + str(list(AVAILABLE_COINS.keys())))

    coin_arg = sys.argv[1]
    if not coin_arg in AVAILABLE_COINS:
        sys.exit("[ERROR] - " + coin_arg + " is not in " + str(list(AVAILABLE_COINS.keys())))

    COIN = AVAILABLE_COINS[coin_arg]
    main(COIN['bot_pair'], COIN['quantity'], 0.99, 1.012)
