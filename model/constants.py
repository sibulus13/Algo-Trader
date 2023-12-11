SYMBOL_CONSTANTS = {
    'AAPL': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.8,
        'high_percentage': 1.03
    },
    'ADBE': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.98,
        'high_percentage': 1.03
    },
    'AMZN': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.98,
        'high_percentage': 1.03
    },
    # 'AURC': {
    #     'model_type': 'DecisionTreeRegressor',
    #     'low_percentage': 0.86,
    #     'high_percentage': 1.12
    # },
    'FB': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.98,
        'high_percentage': 1.03
    },
    'GOOG': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.8,
        'high_percentage': 1.06
    },
    'INVO': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.89,
        'high_percentage': 1
    },
    'MSFT': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.98,
        'high_percentage': 1.03
    },
    'NVDA': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.98,
        'high_percentage': 1.03
    },
    'PYPL': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.98,
        'high_percentage': 1.03
    },
    'TSLA': {
        'model_type': 'DecisionTreeRegressor',
        'low_percentage': 0.98,
        'high_percentage': 1.06
    },
    # 'UFAB': {
    #     # Model price is in the 0.22 range, too much discrepancies with market fill threshold
    #     'model_type': 'DecisionTreeRegressor',
    #     'low_percentage': 0.89,
    #     'high_percentage': 1.24
    # },
}

trades_headers = [
    'last_time_stamp', 'current utc time', 'brought?', 'low_prediction',
    'high_prediction', 'sym', 'price'
]
