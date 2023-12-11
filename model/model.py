import pandas as pd
import os
from sklearn.preprocessing import maxabs_scale
import numpy as np
import time
import pickle
from joblib import dump, load
from pathlib import Path
from sklearn.model_selection import train_test_split
# import all regression models for continuous output
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.tree import DecisionTreeRegressor, ExtraTreeRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_score

DATASET_DIR = r'D:\repo\stonks\data\dataset'
models = [
    # LinearRegression(),
    # Ridge(),
    # Lasso(),
    # ElasticNet(),
    DecisionTreeRegressor(),
    ExtraTreeRegressor(),
    # HistGradientBoostingRegressor(),
]


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


def lenient_accuracy(y_true, y_pred, threshold=0.02):
    '''
    y_true: true values
    y_pred: predicted values
    threshold: threshold for leniency
    
    returns the percentage of predictions that are within the threshold 
    '''
    return np.mean((y_true - y_pred) <= threshold)


def lenient_scorer(estimator, X, y):
    y_pred = estimator.predict(X)
    return lenient_accuracy(y, y_pred)


def model_training(sym, input, output_l, output_h, save=True):
    '''
    Runs through all models and saves the models for each prediction type as well as scoring results in the model folder
    '''
    results = []
    k_fold = KFold(n_splits=5, shuffle=False)
    save = True
    datasets = {'highs': output_h, 'lows': output_l}
    for prediction_type, output in datasets.items():
        x_train, x_test, y_train, y_test = train_test_split(input,
                                                            output,
                                                            test_size=0.2,
                                                            random_state=42)
        for model in models:
            # TODO if model exists, skip, if predictor_info file exist, append results, sort, save
            # start timer
            start = time.time()
            model_name = model.__class__.__name__
            try:
                fitted_model = model.fit(x_train, y_train)
                raw_score = fitted_model.score(x_test, y_test)
                lenient_score = lenient_accuracy(y_test,
                                                 fitted_model.predict(x_test))
                score_k = cross_val_score(model,
                                          x_train,
                                          y_train,
                                          cv=k_fold,
                                          scoring=lenient_scorer)

                # end timer
                end = time.time()
                result = {
                    'model_name': model_name,
                    'prediction_type': prediction_type,
                    'duration': round(end - start, 2),
                    'k_fold_lenient': round(np.mean(score_k), 4),
                    'lenient_score': round(lenient_score, 4),
                    'raw_score': round(raw_score, 4),
                    'comment': '',
                    'model': fitted_model
                }
                s = pickle.dumps(fitted_model)
                if save:
                    dump(
                        result,
                        os.path.join(
                            DATASET_DIR, sym, 'models',
                            f'predictor_{prediction_type}_{model_name}.joblib')
                    )
                    print(f'saved {model_name} predictor_info.joblib')
            except Exception as e:
                print(e)
                # end timer
                end = time.time()
                result = {
                    'model_name': f'{model_name}_{prediction_type}',
                    'prediction_type': prediction_type,
                    'duration': round(end - start, 2),
                    'k_fold_lenient': -1,
                    'lenient_score': -1,
                    'raw_score': -1,
                    'comment': e,
                }
            finally:
                results.append(result)
    # save result to csv
    result = pd.DataFrame(results)
    result = result.sort_values(
        by=['k_fold_lenient', 'duration', 'lenient_score'], ascending=False)
    # print(result)
    results_without_error = result[result['k_fold_lenient'] != -1]
    print(results_without_error)
    result_path = os.path.join(DATASET_DIR, sym, 'models',
                               'predictor_info.csv')
    results_without_error.to_csv(result_path)
    return results_without_error


if __name__ == '__main__':
    volatile_syms_20230729 = ['AURC', 'BGLC', 'UFAB', 'INVO']
    big_syms = [
        'AAPL', 'MSFT', 'AMZN', 'GOOG', 'FB', 'TSLA', 'NVDA', 'PYPL', 'ADBE'
    ]
    # syms = volatile_syms_20230729 + big_syms
    syms = ['PYPL', 'ADBE']
    for sym in syms:
        print(sym)
        inputs, normalized_inputs, output_h, output_l = preprocessing(sym)
        model_training(sym, inputs, output_l, output_h)