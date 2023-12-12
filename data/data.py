from datetime import datetime, timedelta
import time
import pandas as pd
import numpy as np
import pandas_market_calendars as mcal
import ta
from alpaca_trade_api.rest import REST, TimeFrame
import os
from sklearn.preprocessing import MinMaxScaler, maxabs_scale
import os

FMP_API_KEY = os.environ.get('FMP_API_KEY')
POLYGON_KEY = os.environ.get('POLYGON_KEY')
FINNHUB_KEY = os.environ.get('FINNHUB_KEY')
TWELVEDATA_KEY = os.environ.get('TWELVEDATA_KEY')
ALPHA_VANTAGO_KEY = os.environ.get('ALPHA_VANTAGE_KEY')
NASDAQ_DATA_LINK_KEY = os.environ.get('NASDAQ_DATA_LINK_KEY')
ALPACA_API_KEY= os.environ.get('ALPACA_API_KEY')
ALPACA_S_KEY= os.environ.get('ALPACA_S_KEY')

ALPACA_BASE_URL = 'https://data.alpaca.markets/v2'

DATASET_DIR = r'D:\repo\stonks\data\dataset'
api = REST(ALPACA_API_KEY, ALPACA_S_KEY, ALPACA_BASE_URL, api_version='v2')


def raw_csv_path(sym):
    return os.path.join(DATASET_DIR, sym, 'data', f'{sym}.csv')


def data_csv_path(sym):
    return os.path.join(DATASET_DIR, sym, 'data', f'{sym}_data.csv')


def file_path(sym, type, file_type='csv', dir=DATASET_DIR, dir_type='data'):
    return os.path.join(dir, sym, dir_type, f'{sym}_{type}.{file_type}')


def add_unix(df):
    df['timestamp'] = df.index
    df['unixTime'] = [time.mktime(ts.timetuple()) for ts in df['timestamp']]
    return df


def get_last_available_day(timestamp_str: str):
    '''fetches the date of the last available trading day'''
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d')
    day_before = timestamp - timedelta(days=1)
    timestamp_str = day_before.strftime('%Y-%m-%d')
    return timestamp_str


def create_output(data, num_days=5):
    # Create output columns for high and low range of 15 days
    data_points_per_day = 447
    indexer = pd.api.indexers.FixedForwardWindowIndexer(window_size=num_days *
                                                        data_points_per_day)
    data[f'highest_in_{num_days}_days'] = data['high'].rolling(
        window=indexer, min_periods=1).max()
    data[f'lowest_in_{num_days}_days'] = data['low'].rolling(
        window=indexer, min_periods=1).min()
    return data


def fetch_new_data(sym,
                   start_date,
                   end_date=None,
                   save=True,
                   header=True,
                   mode='w',
                   adj='raw',
                   tf=TimeFrame.Minute):
    '''
    Grabs last recorded date from CSV and fetches new data from that date to today
    Saves all datasets and latest scaled entry with corresponding timestamp
    '''
    old_data = pd.DataFrame()
    print(f'fetching new data for {sym}')
    try:
        old_data = pd.read_csv(raw_csv_path(sym))
        # last_recorded_timestamp = old_data.iloc[-1]['timestamp'][:10]
        start_date = old_data.iloc[-1]['timestamp'][:10]
        start_date = get_last_available_day(start_date)
        print(f'recorded day before start date: {start_date}')

    except Exception as e:
        print(f'ERROR: {e}')
        print('no old data found')
    # get new data here
    # print('fetching new data')
    data = api.get_bars(sym,
                        tf,
                        start=start_date,
                        end=end_date,
                        adjustment=adj).df
    data = add_unix(data)
    print(data.shape)
    # print(data.head(1))
    # print(data.tail(1))
    if data.empty:
        return
    # print('cleaning raw data')
    all_data = pd.concat([data,
                          old_data]).drop_duplicates().reset_index(drop=True)
    all_data.sort_values(by=['unixTime'], inplace=True)
    all_data = all_data[all_data.columns.drop(
        list(all_data.filter(regex='Unnamed')))]
    # TODO validate data sparsity

    # create outputs
    # print('creating additional data')
    all_data_with_outputs = create_output(all_data)

    # grab technical indicators
    all_data_with_ta_and_outputs = ta.add_all_ta_features(
        all_data_with_outputs,
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume")

    # all_data_with_ta_and_outputs
    # remove first 50 rows to remove null values from technical indicators
    all_data_with_ta_and_outputs = all_data_with_ta_and_outputs.iloc[
        50:].reset_index(drop=True)
    last_time_stamp = all_data_with_ta_and_outputs.iloc[-1]['timestamp']
    last_unix = all_data_with_ta_and_outputs.iloc[-1]['unixTime']
    # clean up data
    # print('cleaning up data')
    # normalize outputs by dividing by close
    all_data_with_ta_and_outputs[
        'highest_in_5_days_percent'] = all_data_with_ta_and_outputs[
            'highest_in_5_days'] / all_data_with_ta_and_outputs['close']
    all_data_with_ta_and_outputs[
        'lowest_in_5_days_percent'] = all_data_with_ta_and_outputs[
            'lowest_in_5_days'] / all_data_with_ta_and_outputs['close']
    # remove columns timestamp, unixTime, and the index
    outputs = all_data_with_ta_and_outputs[[
        'close', 'highest_in_5_days', 'highest_in_5_days_percent',
        'lowest_in_5_days', 'lowest_in_5_days_percent'
    ]]
    inputs = all_data_with_ta_and_outputs.drop(columns=[
        'timestamp', 'unixTime', 'highest_in_5_days', 'lowest_in_5_days',
        'highest_in_5_days_percent', 'lowest_in_5_days_percent'
    ])
    inputs.dropna(inplace=True, axis=1)
    # print(inputs.columns)
    inputs = inputs.set_index('open')
    # .drop(columns=['Unnamed: 0']).values
    print('inputs.shape', inputs.shape)
    # is any data not legal?
    inputs = inputs.replace([np.inf, -np.inf], np.nan)

    scaled_inputs = maxabs_scale(inputs, axis=0)
    last_scaled_input = scaled_inputs[-1]
    # save data to csv
    if save:
        path = os.path.join(DATASET_DIR, sym, 'data')
        os.makedirs(path, exist_ok=True)
        path = os.path.join(DATASET_DIR, sym, 'models')
        os.makedirs(path, exist_ok=True)
        print('saving to csv')
        all_data.to_csv(raw_csv_path(sym), mode=mode, header=header)
        all_data_with_ta_and_outputs.to_csv(data_csv_path(sym),
                                            mode=mode,
                                            header=header)
        inputs.to_csv(file_path(sym, 'inputs_raw'), mode=mode, header=header)
        # scaled_inputs.to_csv(file_path(sym, 'inputs_scaled'),
        #                      mode=mode,
        #                      header=header)
        outputs.to_csv(file_path(sym, 'outputs_raw'), mode=mode, header=header)
        with open(file_path(sym, 'last_unix', 'txt'), 'w') as f:
            f.write(str(last_unix))
        np.savetxt(file_path(sym, 'last_scaled_input', 'txt'),
                   last_scaled_input,
                   fmt='%d')
        # savve last entry of scaled_inputs to csv
    print(f'done data fetching for {sym}')
    print('-----------------------------------------')
    return last_time_stamp, last_scaled_input


if __name__ == '__main__':
    volatile_syms_20230729 = ['AURC', 'BGLC', 'UFAB', 'INVO']
    big_syms = ['AAPL', 'MSFT', 'AMZN', 'GOOG', 'FB', 'TSLA', 'NVDA', 'PYPL', 'ADBE']
    syms = big_syms
    for sym in syms:
        # sym = 'AAPL'
        start_date = '2000-01-01'
        fetch_new_data(sym, start_date=start_date)