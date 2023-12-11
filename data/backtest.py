from sklearn.preprocessing import maxabs_scale
import numpy as np
import pandas as pd
import os
from joblib import load

DATASET_DIR = r'D:\repo\stonks\data\dataset'


def file_path(sym,
              data_type=None,
              file_type='csv',
              dir=DATASET_DIR,
              dir_type='data'):
    if not data_type:
        return os.path.join(dir, sym, dir_type, f'{sym}.{file_type}')
    return os.path.join(dir, sym, dir_type, f'{sym}_{data_type}.{file_type}')


def preprocessing(sym):
    '''
    takes in related inputs and outputs for a symbol and returns the preprocessed data
    '''
    input_df = pd.read_csv(file_path(sym, 'inputs_raw'))
    output_df = pd.read_csv(file_path(sym, 'outputs_raw'))
    input_df.dropna(inplace=True, axis=1)
    input = input_df.set_index('open').drop(columns=['Unnamed: 0'],
                                            errors='ignore').values
    normalized_input = maxabs_scale(input, axis=0)
    output_h = output_df['highest_in_5_days_percent'].values
    output_l = output_df['lowest_in_5_days_percent'].values
    return input, normalized_input, output_h, output_l


def load_model(sym='AAPL',
               model_type='DecisionTreeRegressor',
               output_type='lows'):
    path = rf'D:\repo\stonks\data\dataset\{sym}\models\predictor_{output_type}_{model_type}.joblib'
    print(path)
    predictor_info = load(path)
    return predictor_info


def run_back_test(X,
                  predictor_h,
                  predictor_l,
                  gain_ratio=1.5,
                  min_gain_ratio=1.1,
                  max_loss_ratio=0.9,
                  buy_threshold=0):
    '''
    Tests prediction model based on gain factor and safety margin
    Assumes using bracket order
    gain_ratio: gain factor to sell
    min_gain_ratio: minimum gain factor to buy
    max_loss_ratio: maximum loss factor to buy
    '''
    brought = False
    buy_counter = 0
    brought_prices = []
    brought_index = []
    sold_prices = []
    sold_index = []
    brought_margins = []
    gains = []

    for index, row in enumerate(X):
        # 0=open, 1=high, 2=low, 3=close, 4=volume
        closed_price = row[2]
        if brought:
            # Stop Loss
            stop_loss = closed_price <= (brought_prices[-1] *
                                         brought_margins[-1][0])
            take_profit = closed_price >= (brought_prices[-1] *
                                           brought_margins[-1][1])
            if stop_loss or take_profit:
                # print('stop_loss', stop_loss, 'take_profit', take_profit, 'closed_price', closed_price, 'brought_price', brought_prices[-1], 'gain', closed_price/brought_prices[-1])
                sold_prices.append(closed_price)
                sold_index.append(index)
                gains.append(sold_prices[-1] / brought_prices[-1])
                brought = False
                # print('sold @ ', closed_price, 'brought @ ', brought_prices[-1], 'gain = ', closed_price/brought_prices[-1])
            else:
                continue

        input = row.reshape(1, -1)
        low_prediction = predictor_l['model'].predict(input)[0]
        high_prediction = predictor_h['model'].predict(input)[0]
        gain = round(high_prediction / low_prediction, 2)
        gain_ratio_achieved = gain >= gain_ratio
        min_gain_ratio_achieved = high_prediction >= min_gain_ratio
        max_loss_ratio_overcomed = low_prediction >= max_loss_ratio
        if not brought:
            buy_counter += 1
            if gain_ratio_achieved and min_gain_ratio_achieved and max_loss_ratio_overcomed and buy_counter >= buy_threshold:
                brought = True
                # print('brought @ ', closed_price)
                brought_prices.append(closed_price)
                brought_index.append(index)
                brought_margins.append([low_prediction, high_prediction])
                buy_counter = 0
    gain = np.prod(gains)
    NUM_POINTS_PER_DAY = 447
    num_days = len(X) / NUM_POINTS_PER_DAY
    return brought_prices, sold_prices, brought_index, sold_index, brought_margins, gains, gain, num_days, gain / num_days


def back_test(sym):
    input, normalized_input, output_h, output_l = preprocessing(sym)
    predictor_l = load_model(sym, 'DecisionTreeRegressor', 'lows')
    predictor_h = load_model(sym, 'DecisionTreeRegressor', 'highs')
    backtests = []
    for gain_ratio in [1]:
        # for min_gain_ratio in [0.5]:
        for min_gain_ratio in np.arange(1, 2, 0.03):
            # for max_loss_ratio in [1]:
            brought_prices = []
            for max_loss_ratio in np.arange(0.8, 1.1, 0.03):
                brought_prices, sold_prices, brought_index, sold_index, brought_margins, gains, gain, num_days, gain_per_day = run_back_test(
                    input,
                    predictor_h,
                    predictor_l,
                    gain_ratio=gain_ratio,
                    min_gain_ratio=min_gain_ratio,
                    max_loss_ratio=max_loss_ratio,
                    buy_threshold=0)
                if brought_prices:
                    score = {
                        'gain_ratio': gain_ratio,
                        'min_gain_ratio': min_gain_ratio,
                        'max_loss_ratio': max_loss_ratio,
                        'gain': gain,
                        'num_days': num_days,
                        'gain_per_day': gain_per_day,
                        'num_of_trades': len(sold_prices),
                        'brought_prices': brought_prices,
                        'sold_prices': sold_prices,
                        'brought_index': brought_index,
                        'sold_index': sold_index,
                        'brought_margins': brought_margins,
                        'gains': gains
                    }
                    backtests.append(score)
                    print(sym)
                    print(
                        f'min_gain_ratio:',
                        min_gain_ratio,
                        'max_loss_ratio:',
                        max_loss_ratio,
                    )
                    print(
                        f'total gain achieved: {gain} over ~{num_days} days -> {gain/num_days}/day'
                    )
                    print(
                        f'Number of trades: {len(gains)} -> gain per trade: {gain/len(gains)}'
                    )
                    print()

            if not brought_prices:
                # skip inner loop if nothing was brought, assuming no trades made
                continue

    print('num of scores:', len(backtests))
    backtests_df = pd.DataFrame(backtests).sort_values('gain', ascending=False)
    backtests_df.to_csv(rf'D:\repo\stonks\data\dataset\{sym}\backtests.csv',
                        index=False)
    print(backtests_df[[
        'gain',
        'gain_per_day',
        'num_days',
        'num_of_trades',
        'min_gain_ratio',
        'max_loss_ratio',
    ]])
    best_gain = backtests_df.iloc[0]['gains']
    best_num_days = backtests_df.iloc[0]['num_days']
    best_gain_per_day = backtests_df.iloc[0]['gain_per_day']
    print(type(best_gain), len(best_gain))
    print(f'Average gain per trade of best gain: {np.mean(best_gain)}')
    print(
        f'Best total gain: {np.prod(best_gain)} achieved over {best_num_days} days -> {best_gain_per_day}/day'
    )
    print()
    print()


if __name__ == '__main__':
    volatile_syms_20230729 = ['AURC', 'BGLC', 'UFAB', 'INVO']
    big_syms = [
        'AAPL', 'MSFT', 'AMZN', 'GOOG', 'FB', 'TSLA', 'NVDA', 'PYPL', 'ADBE'
    ]
    # syms = volatile_syms_20230729 + big_syms
    syms = ['AURC']
    for sym in syms:
        print(sym)
        back_test(sym)