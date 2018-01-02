from copy import copy
from typing import List

from money import Money

from .order import Order


class Trade():
    def __init__(self, input: Money, output: Money, market: 'Market', orders: List[Order]=None, previous_trade: 'Trade'=None):
        self.input  = Order.quantize(input)
        self.output = Order.quantize(output)
        self.market = market
        self.orders = orders
        if previous_trade: self.history = copy(previous_trade.history) + [self]
        else:              self.history = [self]


    @property
    def amount(self):
        """ Duck type Money """
        return self.output.amount


    @property
    def currency(self):
        """ Duck type Money """
        return self.output.currency

    def __eq__(self, other):
        for key in ["input", "output", "market", "orders", "history"]:
            if getattr(self, key) != getattr(other, key):
                return False
        return True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        coins  = [ self.history[0].input ] + [ trade.output for trade in self.history ]
        output = " -> ".join(map(str, coins))
        return output