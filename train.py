from data.data import fetch_new_data
from model.model import preprocessing, model_training
from data.backtest import back_test

if __name__ == '__main__':
    volatile_syms_20230729 = ['AURC', 'BGLC', 'UFAB', 'INVO']
    big_syms = [
        'AAPL', 'MSFT', 'AMZN', 'GOOG', 'FB', 'TSLA', 'NVDA', 'PYPL', 'ADBE'
    ]
    # syms = volatile_syms_20230729 + big_syms
    syms = ['AMZN', 'GOOG', 'FB', 'TSLA', 'NVDA', 'PYPL', 'ADBE']
    start_date = '2000-01-01'
    for sym in syms:
        print(sym)
        # fetch_new_data(sym, start_date=start_date)
        inputs, normalized_inputs, output_h, output_l = preprocessing(sym)
        model_training(sym, inputs, output_l, output_h)
        back_test(sym)