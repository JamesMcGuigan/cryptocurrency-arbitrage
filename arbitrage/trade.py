from copy import copy
from decimal import Decimal
from typing import List, Optional

from money import Money

from .order import Order


class Trade():
    def __init__(self, input: Money, output: Money, market: 'Market', orders: List[Order]=None, previous_trade: 'Trade'=None):
        self.input  = Order.quantize(input)
        self.output = Order.quantize(output)
        self.market = market
        self.orders = orders
        self.orders_combined = Order.combined(orders)
        if previous_trade: self.history = copy(previous_trade.history) + [self]
        else:              self.history = [self]


    @property
    def profit_absolute(self) -> Optional[Money]:
        try:
            return self.history[-1].output - self.history[0].input
        except:
            return None

    @property
    def profit_percent(self) -> Optional[Money]:
        if self.profit_absolute is None: return None
        return self.history[-1].output.amount / self.history[0].input.amount


    @property
    def amount(self) -> Decimal:
        """ Duck type Money """
        return self.output.amount


    @property
    def currency(self) -> str:
        """ Duck type Money """
        return self.output.currency

    def __eq__(self, other):
        for key in ["input", "output", "market", "orders", "history"]:
            if getattr(self, key) != getattr(other, key):
                return False
        return True

    def __repr__(self):
        coins  = [ self.history[0].input ] + [ trade.output for trade in self.history ]
        output = " -> ".join(map(str, map(Order.quantize, coins)))
        return output

    def __str__(self):
        output = "\n".join([
            self.market['exchange'] + ": profit = " + str(self.profit_absolute) + " ("+str(self.profit_percent)+"%)",
            self.__repr__(),
            "\n".join([ str(trade.orders_combined) for trade in list(self.history) ]),
        ])
        return output