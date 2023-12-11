from data.data import fetch_new_data
from bot.bot import connect_trader_workstation, buy
from gui.main import pop_up
from gui.utils import notify
from model.constants import SYMBOL_CONSTANTS, trades_headers
from joblib import load
import datetime
import time
import pytz
from bot.recorder import write_to_csv

# TODO ERRORS
#     # X has 79 features, but DecisionTreeRegressor is expecting 86 features as input.
#     # 'str' object has no attribute 'to_pydatetime'


def strategy(app, sym, p_low, p_high):
    start_date = '2000-01-01'
    last_time_stamp, last_scaled_input = fetch_new_data(sym,
                                                        start_date,
                                                        save=True)
    print('newest data for ', sym, 'is')
    print(last_time_stamp)
    # print(last_scaled_input)
    last_scaled_input = last_scaled_input.reshape(1, -1)
    # print(last_scaled_input)
    try:
        low_prediction = p_low['model'].predict(last_scaled_input)[0]
        high_prediction = p_high['model'].predict(last_scaled_input)[0]
    except Exception as e:
        # dealing with X has 76 features, but DecisionTreeRegressor is expecting 83 features as input.
        print(e)
        low_prediction = -1
        high_prediction = -1
    trade_path = rf'D:\repo\stonks\data\dataset\{sym}\trades.csv'
    print('current results')
    print(low_prediction, high_prediction)
    print(last_time_stamp, type(last_time_stamp))

    # if the last time stamp is within 30min of the current time, then run the bot
    # if not valid_time(last_time_stamp):
    #     data = {
    #         'last_time_stamp': last_time_stamp,
    #         'current utc time': datetime.datetime.now(datetime.timezone.utc),
    #         'brought?': 'Time out of scope',
    #         'low_prediction': low_prediction,
    #         'high_prediction': high_prediction,
    #         'sym': sym,
    #         'price': 'none'
    #     }
    #     write_to_csv(trade_path, data, header=trades_headers)
    #     return False

    if acceptable_prediction(sym, low_prediction, high_prediction):
        notify()
        price_confirmer = pop_up(sym, low_prediction, high_prediction)
        low, price, high = price_confirmer.low, price_confirmer.price, price_confirmer.high
        print(low, price, high, 'prices')
        price = {
            'stop_loss_price': float(low),
            'price': float(price),
            'take_profit_price': float(high),
        }
        print(price)
        buy(app, sym, price)
        data = {
            'last_time_stamp': last_time_stamp,
            'current utc time': datetime.datetime.now(datetime.timezone.utc),
            'brought?': 'buy',
            'low_prediction': low_prediction,
            'high_prediction': high_prediction,
            'sym': sym,
            'price': 'none'
        }
    else:
        data = {
            'last_time_stamp': last_time_stamp,
            'current utc time': datetime.datetime.now(datetime.timezone.utc),
            'brought?': 'no buy',
            'low_prediction': low_prediction,
            'high_prediction': high_prediction,
            'sym': sym,
            'price': 'none'
        }
    write_to_csv(trade_path, data, header=trades_headers)
    return True


def load_model(sym='AAPL',
               model_type='DecisionTreeRegressor',
               output_type='lows'):
    path = rf'D:\repo\stonks\data\dataset\{sym}\models\predictor_{output_type}_{model_type}.joblib'
    # print(path)
    predictor_info = load(path)
    return predictor_info


def valid_time(last_time_stamp):
    '''Compare last_time_stamp to current time and return True if within 30min'''
    current_time = datetime.datetime.now(datetime.timezone.utc)
    try:
        # catches date string parsing errors and just skip the bot strategy
        if type(last_time_stamp) == str:
            last_time = datetime.datetime.strptime(last_time_stamp,
                                                   '%Y-%m-%d %H:%M:%S%z')
        else:
            last_time = last_time_stamp.to_pydatetime()
        print(type(last_time_stamp))
        print(e)
        last_time = last_time_stamp
        print(f'Current Time: {current_time}')
        print(f'Last Time: {last_time}')
        # print(type(last_time), type(current_time))
        if (current_time - last_time) < datetime.timedelta(minutes=30):
            print('Last time stamp is within 30min of current time')
            return True
        return False
    except Exception as e:
        return False


def acceptable_prediction(sym, low_prediction, high_prediction):
    if low_prediction >= SYMBOL_CONSTANTS[sym][
            'low_percentage'] and high_prediction >= SYMBOL_CONSTANTS[sym][
                'high_percentage']:
        print('Acceptable prediction with low_prediction: ', low_prediction,
              ' and high_prediction: ', high_prediction)
        return True
    return False


def run_bot(app=None, syms=['AAPL']):
    # app.reqGlobalCancel()  #cancels all orders
    app, thread = connect_trader_workstation()
    try:
        while 1:
            app, thread = connect_trader_workstation(app, thread)
            for sym in syms:
                # sym = syms[0]
                predictor_low = load_model(
                    sym=sym,
                    output_type='lows',
                    model_type=SYMBOL_CONSTANTS[sym]['model_type'])
                predictor_high = load_model(
                    sym=sym,
                    output_type='highs',
                    model_type=SYMBOL_CONSTANTS[sym]['model_type'])
                strategy(app, sym, predictor_low, predictor_high)
    except Exception as e:
        print(e)
        notify()
    finally:
        print('finally')
        app.disconnect()


if __name__ == '__main__':
    run_bot(syms=SYMBOL_CONSTANTS.keys())
