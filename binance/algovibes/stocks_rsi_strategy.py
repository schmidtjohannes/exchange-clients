# from https://youtu.be/pB8eJwg7LJU
# thanks algovibes
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
pd.options.mode.chained_assignment = None


def RSIcalc(asset):
    df = yf.download(asset, start='2011-01-01')
    df['MA200'] = df['Adj Close'].rolling(window=200).mean()
    df['price change'] = df['Adj Close'].pct_change()
    df['Upmove'] = df['price change'].apply(lambda x: x if x > 0 else 0)
    df['Downmove'] = df['price change'].apply(lambda x: abs(x) if x < 0 else 0)
    df['avg Up'] = df['Upmove'].ewm(span=19).mean()
    df['avg Down'] = df['Downmove'].ewm(span=19).mean()
    df.dropna(inplace=True)
    df['RS'] = df['avg Up']/df['avg Down']
    df['RSI'] = df['RS'].apply(lambda x: 100-(100/(x+1)))
    df.loc[(df['Adj Close'] > df['MA200']) & (df['RSI'] < 30), 'Buy'] = 'Yes'
    df.loc[(df['Adj Close'] < df['MA200']) | (df['RSI'] > 30), 'Buy'] = 'No'
    return df

def getSignals(df):
    Buying_dates, Selling_dates = [], []
    for i in range(len(df)):
        if "Yes" in df['Buy'].iloc[i]:
            Buying_dates.append(df.iloc[i+1].name)
            for j in range(1,11):
                if df['RSI'].iloc[i + j] > 40:
                    Selling_dates.append(df.iloc[i+j+1].name)
                    break
                elif j == 10:
                    Selling_dates.append(df.iloc[i+j+1].name)
    return Buying_dates, Selling_dates


tickers = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
tickers = tickers.Symbol.to_list()

for i,v in enumerate(tickers):
    tickers[i] = v.replace('.','-')

frame = RSIcalc(tickers[0])
buy, sell = getSignals(frame)

# plt.figure(figsize=(12,5))
# plt.scatter(frame.loc[buy].index, frame.loc[buy]['Adj Close'], marker="^", color='g')
# plt.plot(frame['Adj Close'], alpha=0.7)
# plt.show()

Profits = (frame.loc[sell].Open.values - frame.loc[buy].Open.values) / frame.loc[buy].Open.values

print(Profits)

wins = [i for i in Profits if i > 0]

print(wins)

win_rate = len(wins) / len(Profits)

matrixsignals = []
matrixprofits = []

# for i in range(len(tickers)):
#     frame = RSIcalc(tickers[i])
#     buy,sell = getSignals(frame)
#     Profits = (frame.loc[sell].Open.values - frame.loc[buy].Open.values) / frame.loc[buy].Open.values
#     matrixsignals.append(buy)
#     matrixprofits.append(Profits)

print(matrixsignals)
print(matrixprofits)

# avgs = %  of profit , then . mean()

# then sum(avgs)/len(avgs)


allprofit = []
for i in matrixprofits:
    for e in i:
        allprofit.append(e)

all_wins = [i for i in allprofit if i > 0]

print(len(all_wins)/len(allprofit))

plt.hist(allprofit, bins=100)
plt.show()