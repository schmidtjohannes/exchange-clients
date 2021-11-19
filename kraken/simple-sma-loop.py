import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd
import time
from datetime import datetime
import sys

INTERVAL_IN_MIN = 15
ETHUSD_COIN = {
  "bot_pair": "ETHUSD",
  "quantity": 0.01
}

DOTUSD_COIN = {
  "bot_pair": "DOTUSD",
  "quantity": 1
}

MANAUSD_COIN = {
  "bot_pair": "MANAUSD",
  "quantity": 7
}

LRCUSD_COIN = {
  "bot_pair": "LRCUSD",
  "quantity": 15
}

COIN = {}

AVAILABLE_COINS = { "MANA" : MANAUSD_COIN , "DOT" : DOTUSD_COIN, "ETH" : ETHUSD_COIN , "LRC" : LRCUSD_COIN }

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

def get_sma_closes(coin):
    unixtime = time.time() - (60 * 60 * INTERVAL_IN_MIN)
    try:
        ohlc, last = k.get_ohlc_data(coin, interval=INTERVAL_IN_MIN, since=unixtime)
    except:
        time.sleep(5)
        ohlc, last = k.get_ohlc_data(coin, interval=INTERVAL_IN_MIN, since=unixtime)
    return SMA(ohlc)

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
    txid = k.query_orders_info(order['txid'][0]).iloc[0]['trades'][0]
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
        SMA_closes = get_sma_closes(coin)
        shortTerm, longTerm = get_current_sma_values(SMA_closes)
        print('shortTerm ' + str(shortTerm))
        print('longTerm ' + str(longTerm))
        time.sleep(5)
        if shortTerm >= longTerm:
            order = create_order(qty, type='buy')
            open_position = True
            time.sleep(5)
        if open_position:
            while True:
                print('\nCheck SELL at ' + get_time())
                # let's wait one interval before start checking
                if order['transactTime'] + (60 * INTERVAL_IN_MIN) > time.time():
                    print('Sleep until initial INTERVAL is over')
                    time.sleep(15)
                    continue
                SMA_closes = get_sma_closes(coin)
                time.sleep(1)
                current_close = get_current_close(coin)
                print('current_close ' + str(current_close))
                print('order[price] ' + str(order['price']))
                print('shortTerm ' + str(shortTerm))
                print('longTerm ' + str(longTerm))
                shortTerm, longTerm = get_previous_sma_values(SMA_closes)
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

    
    if len(sys.argv) != 2:
        sys.exit("[ERROR] - No coin passed, avialable coins: " + str(list(AVAILABLE_COINS.keys())))

    coin_arg = sys.argv[1]
    if not coin_arg in AVAILABLE_COINS:
        sys.exit("[ERROR] - " + coin_arg + " is not in " + str(list(AVAILABLE_COINS.keys())))

    COIN = AVAILABLE_COINS[coin_arg]
    main(COIN['bot_pair'], COIN['quantity'], 0.99, 1.01)
