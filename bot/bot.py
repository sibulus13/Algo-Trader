import random
import multiprocessing
import sys
import pprint

import threading
import time

# from ibapi.order import *
# from ibapi.client import EClient
# from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

from .constants import *
from .IBAPI import IBapi

# A strategy should involve
#   checking if the targetted stock is brought
#   check if last transaction fell below terminating threshold
#   decision making process to determine if the stock should be brought
#   buy the stock if it should be brought and is not already brought
#   updating brought status of the stock


def connect_trader_workstation(app=None, api_thread=None):
    '''
    returns trader workstation connection
    '''
    if app and app.isConnected():
        return app, api_thread
    seconds_spent_disconnected = 0
    while True:
        app = IBapi()
        app.nextorderId = None
        app.connect('127.0.0.1', 7497, 123)

        # Start the socket in a thread
        api_thread = threading.Thread(target=app.run, daemon=True)
        api_thread.start()
        # print(app.nextorderId)
        # print(app.isConnected())
        # Check if the API is connected via orderid
        # if isinstance(app.nextorderId, int):
        if app.isConnected():
            print('connected')
            # print()
            return app, api_thread
        else:
            seconds_spent_disconnected += 1
            print(f'{seconds_spent_disconnected} seconds spent disconnected')
            time.sleep(10)


def addAttr(cls: classmethod, values: dict):
    '''
    Sets attributes of a class from a dictionary
    '''
    for k, v in values.items():
        setattr(cls, k, v)


def buy(app, sym: str, price: dict):
    '''
    issues bracket order on contract
    buys 1 share of sym
    '''
    # Create a contract
    contract = Contract()
    contract.symbol = sym
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    parentOrderId = app.nextOrderId()
    action = 'BUY'
    quantity = 1

    # Create a bracket order
    limitPrice = price['price'] or 0
    takeProfitLimitPrice = price['take_profit_price']
    stopLossPrice = min(price['stop_loss_price'], 0.98 * limitPrice)
    bracketOrder = BracketOrder(parentOrderId, action, quantity, limitPrice,
                                takeProfitLimitPrice, stopLossPrice)
    for order in bracketOrder:
        print('Placing order: ', order)
        app.placeOrder(order.orderId, contract, order)
        app.nextOrderId()


def match_price_variation(price, min_price_variation=0.05):
    '''
    returns price that is a multiple of min_price_variation
    '''
    q, _ = divmod(price, min_price_variation)
    less = q * min_price_variation
    more = (q + 1) * min_price_variation
    if abs(price - more) <= abs(price - less):
        return less
    return more


def check_statuses():
    # Call reqAccountUpdates

    # Poll updates from Ewrapper::updateAccountValue
    return []


def get_portfolio(app):
    app.reqAccountUpdates(subscribe=True, acctCode=app.ACC_CDE)
    time.sleep(1)
    # print(app.portfolio)
    return app.portfolio


def get_brought_stock_list(app):
    '''
    returns list of stocks that are brought
    '''
    app.reqOpenOrders()
    time.sleep(1)
    app.reqCompletedOrders(True)
    time.sleep(1)
    return app.open_orders


def get_unbrought_stock_list(portfolio: dict) -> list:
    '''
    returns list of stocks that are not brought
    '''
    unbrought_stocks = []
    print(f'portfolio: {portfolio}')
    # TODO need to check if the portfolio position is 0
    for stock in STOCK_LIST:
        if stock in portfolio.keys():
            if portfolio[stock]['position'] > 0:
                # stock is brought
                continue
        unbrought_stocks.append(stock)
    print(f'unbrought_stocks: {unbrought_stocks}')
    return unbrought_stocks


def get_unordered_stock_list(unbrought: list, ordered: dict) -> list:
    '''
    returns list of stocks that are not ordered
    '''
    unordered = []
    print(f'unbrought: {unbrought}')
    for stock in unbrought:
        if stock in ordered.keys():
            continue
        unordered.append(stock)
    print(f'unordered: {unordered}')
    return unordered


def BracketOrder(parentOrderId: int, action: str, quantity: int,
                 limitPrice: float, takeProfitLimitPrice: float,
                 stopLossPrice: float):
    # This will be our main or "parent" order
    parent = Order()
    parent.orderId = parentOrderId
    parent.action = action
    parent.orderType = "LMT"
    parent.totalQuantity = quantity
    parent.lmtPrice = match_price_variation(limitPrice)
    parent.eTradeOnly = False
    parent.firmQuoteOnly = False
    parent.transmit = False

    takeProfit = Order()
    takeProfit.orderId = parent.orderId + 1
    takeProfit.action = "SELL"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = match_price_variation(takeProfitLimitPrice)
    takeProfit.auxPrice = match_price_variation(
        takeProfitLimitPrice)  #trigger price
    takeProfit.tif = "GTC"
    takeProfit.parentId = parentOrderId
    takeProfit.transmit = False
    takeProfit.eTradeOnly = False
    takeProfit.firmQuoteOnly = False

    stopLoss = Order()
    stopLoss.orderId = parent.orderId + 2
    stopLoss.action = "SELL"
    stopLoss.orderType = "STP"
    stopLoss.tif = "GTC"
    # Stop trigger price
    stopLoss.auxPrice = match_price_variation(stopLossPrice)
    stopLoss.totalQuantity = quantity
    stopLoss.parentId = parentOrderId
    stopLoss.eTradeOnly = False
    stopLoss.firmQuoteOnly = False
    stopLoss.transmit = True

    bracketOrder = [parent, takeProfit, stopLoss]
    return bracketOrder


def Bot(app):
    # TODO is there a need to check untransmitted orders?
    portfolio = get_portfolio(app)
    not_owned_stocks = get_unbrought_stock_list(portfolio)

    ordered_stocks = get_brought_stock_list(app)
    unordered_stocks = not_owned_stocks
    # TODO use unordered_stocks again once algo is tested and works sufficiently
    # unordered_stocks = get_unordered_stock_list(not_owned_stocks,
    #                                             ordered_stocks)
    for stock in unordered_stocks:
        print(f'should I buy {stock}?')
        # get stock's current price
        prices = app.get_stock_price(stock)
        print(prices)
        # buy stock if it should be bought
        buy(app, stock, prices)


if __name__ == '__main__':
    app, _ = connect_trader_workstation()
    # run_bot(app)
    print('end')