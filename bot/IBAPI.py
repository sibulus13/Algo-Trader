from ibapi.order import *
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.ticktype import TickTypeEnum
from ibapi.common import BarData
from ibapi.execution import Execution
from ibapi.order_state import OrderState

from .recorder import *
from .constants import *

import time
import os


class IBapi(EWrapper, EClient):
    account_info = {}
    portfolio = {}
    open_orders = {}
    ACC_CDE = 'DU5950392'
    CASHBALANCE = 'CashBalance'
    CURRENCY = '$CAD'
    stock = {}  # stock[symbol] = used to fetch queried stock prices

    def __init__(self):
        EClient.__init__(self, self)

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        # print('The next valid order id is: ', self.nextorderId)

    def nextOrderId(self):
        new = self.nextorderId + 1
        self.nextValidId(new)
        return self.nextorderId

    def updatePortfolio(self, contract: Contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):
        # Callback from reqAccountUpdates which fetches list of
        super().updatePortfolio(contract, position, marketPrice, marketValue,
                                averageCost, unrealizedPNL, realizedPNL,
                                accountName)
        # print("UpdatePortfolio.", "Symbol:", contract.symbol, "SecType:",
        #       contract.secType, "Exchange:", contract.exchange, "Position:",
        #       position, "MarketPrice:", marketPrice, "MarketValue:",
        #       marketValue, "AverageCost:", averageCost, "UnrealizedPNL:",
        #       unrealizedPNL, "RealizedPNL:", realizedPNL, "AccountName:",
        #       accountName)
        self.portfolio[contract.symbol] = {
            'position': position,
            'marketPrice': marketPrice,
            'marketValue': marketValue,
            "UnrealizedPNL": unrealizedPNL,
            "RealizedPNL": realizedPNL
        }

    def tickPrice(self, reqId, tickType, price, attrib):
        '''
        Callback from reqMktData which fetches the stock price
        '''
        # print(f'tickprice {tickType} ${price}')
        if tickType == 1:
            self.stock['currentBid'] = price
            return
        if tickType == 2:
            self.stock['currentAsk'] = price
            return
        if tickType == 4:
            self.stock['currentLast'] = price
            return
        if tickType == 6:
            self.stock['currentHigh'] = price
            return
        if tickType == 7:
            self.stock['currentLow'] = price
            return
        if tickType == 9:
            # closing price of previous day
            self.stock['currentClose'] = price
            return
        if tickType == 14:
            # current session opening price
            self.stock['currentOpen'] = price
            return
        # Delayed types
        if tickType == 66:
            self.stock['delayedBid'] = price
            return
        if tickType == 67:
            self.stock['delayedAsk'] = price
            return
        if tickType == 68:
            self.stock['delayedLast'] = price
            return
        if tickType == 72:
            self.stock['delayedHigh'] = price
            return
        if tickType == 73:
            self.stock['delayedLow'] = price
            return
        if tickType == 75:
            self.stock['delayedClose'] = price
            return
        if tickType == 76:
            self.stock['delayedOpen'] = price
            return

    def get_stock_price(self, sym):
        '''
        returns the stock price of sym
        '''
        # Create a contract
        contract = Contract()
        contract.symbol = sym
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        self.reqMarketDataType(3)  # 1 = realtime, 2 = frozen, 3 = delayed
        # Request the price
        self.reqMktData(1, contract, '', False, False, [])
        time.sleep(2)
        return self.stock

    def execDetails(self, reqId: int, contract: Contract,
                    execution: Execution):
        '''
        Callback from reqExecutions which fetches the execution details
        Write the execution details to a csv file based on the symbol
        '''
        super().execDetails(reqId, contract, execution)
        # print("ExecDetails. ReqId:", reqId, "Symbol:", contract.symbol, "SecType:", contract.secType, "Currency:", contract.currency, execution)
        csvFile = os.path.join(os.path.dirname(__file__), 'execHistory',
                               f'{contract.symbol}_exec.csv')
        data = {
            # Contract details
            'symbol': contract.symbol,
            'secType': contract.secType,
            'currency': contract.currency,
            # Execution details
            # 'orderId': execution.orderId,
            # 'clientId': execution.clientId,
            # 'permId': execution.permId,
            'time': execution.time,
            'side': execution.side,
            'price': execution.price,
            'shares': execution.shares,
            'cumqty': execution.cumQty,
            'avgprice': execution.avgPrice,
            'evrule': execution.evRule,
            'lastliquidity': execution.lastLiquidity,
            'contract': contract,
            'execution': execution
        }
        print('execDetails')
        print(data)
        write_to_csv(csvFile, data)

    def openOrder(self, orderId, contract: Contract, order: Order,
                  orderState: OrderState):
        '''
        Callback from reqOpenOrders which fetches the open orders
        Record open orders in the portfolio dictionary
        Save the open orders to a csv file based on the symbol
        '''
        super().openOrder(orderId, contract, order, orderState)
        # print("OpenOrder. PermId:", order.permId, "ClientId:", order.clientId, " OrderId:", orderId),
        #       "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
        #       "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
        #       "TotalQty:", decimalMaxString(order.totalQuantity), "CashQty:", floatMaxString(order.cashQty),
        #       "LmtPrice:", floatMaxString(order.lmtPrice), "AuxPrice:", floatMaxString(order.auxPrice), "Status:", orderState.status,
        #       "MinTradeQty:", order.minTradeQty, "MinCompeteSize:", order.minCompeteSize,
        #       "competeAgainstBestOffset:", "UpToMid" if order.competeAgainstBestOffset == COMPETE_AGAINST_BEST_OFFSET_UP_TO_MID else floatMaxString(order.competeAgainstBestOffset),
        #       "MidOffsetAtWhole:", floatMaxString(order.midOffsetAtWhole),"MidOffsetAtHalf:" ,floatMaxString(order.midOffsetAtHalf))

        # order.contract = contract
        # self.permId2ord[order.permId] = order
        data = {
            'orderId': orderId,
            'contract': contract,
            'order': order,
            'orderState': orderState,
            'completedTime': orderState.completedTime
        }
        print(data)
        self.open_orders[contract.symbol] = data

    def completedOrder(self, contract: Contract, order: Order,
                       orderState: OrderState):
        '''
        Callback from reqCompletedOrders which fetches the completed orders
        '''
        data = {
            'orderId': order.orderId,
            'contract': contract,
            'order': order,
            'orderState': orderState,
            'completedTime': orderState.completedTime
        }
        print('completedOrder')
        print(data)
        # remove the completed order from the open orders if the content of the open order matches data
        if contract.symbol in self.open_orders and self.open_orders[
                contract.symbol] == data:
            del self.open_orders[contract.symbol]
        # Save the completed order to a csv file based on the symbol
        csvFile = os.path.join(os.path.dirname(__file__), 'orderHistory',
                               f'{contract.symbol}_order.csv')
        write_to_csv(csvFile, data, ORDER_CSV_HEADERS)
        return super().completedOrder(contract, order, orderState)