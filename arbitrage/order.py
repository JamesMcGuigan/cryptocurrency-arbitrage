
from copy import copy
from decimal import Decimal
from typing import Union, List

from money import Money
from pydash import py_ as _

satoshi = Decimal('0.00000001')

class Order():

    @classmethod
    def combined(cls, orders: 'List[Order]') -> 'Union[Order, None]':
        if len(orders) == 0: return None

        assert _(orders).map('base_currency').uniq().size().value()   == 1
        assert _(orders).map('quote_currency').uniq().size().value()  == 1
        assert _(orders).map('ask_bid').uniq().size().value()         == 1
        assert _(orders).map('market.symbol').uniq().size().value()   == 1
        assert _(orders).map('market.exchange').uniq().size().value() == 1

        limit_order_price = Money(0, orders[0].quote_currency)
        quote_total_price = Money(0, orders[0].quote_currency)
        base_volume       = Money(0, orders[0].base_currency)

        for order in orders:
            quote_total_price += order.quote_total_price
            base_volume       += order.base_volume
        quote_price_unit = quote_total_price / base_volume.amount

        if orders[0].ask_bid == 'ask': limit_order_price = _(orders).map('quote_unit_price').max().value()
        if orders[0].ask_bid == 'bid': limit_order_price = _(orders).map('quote_unit_price').min().value()

        combined_order = Order(
            raw=[quote_price_unit.amount, base_volume.amount],
            market=orders[0].market,
            ask_bid=orders[0].ask_bid,
            limit_order_price=limit_order_price,
        )
        return combined_order


    def get_minimum_order(self, minimum_order_amount: Money) -> 'Order':
        assert minimum_order_amount.currency in [self.base_currency, self.quote_currency]

        output = copy(self)
        if minimum_order_amount.currency == output.base_currency:
            output.base_volume = minimum_order_amount

        elif minimum_order_amount.currency == output.quote_currency:
            output.quote_volume = minimum_order_amount

        return output


    def with_max_remaining(self, maximum: Money) -> 'Order':
        """
        Return a copy of the order with at most maximum volme
        """
        assert maximum.currency in [self.base_currency, self.quote_currency]

        output = copy(self)
        if maximum.currency == output.base_currency:
            if maximum < output.base_volume:
                output.base_volume = maximum

        elif maximum.currency == output.quote_currency:
            if maximum < output.quote_volume:
                output.quote_volume = maximum

        return output


    @classmethod
    def quantize(cls, money: Money):
        return Money( Decimal(money.amount).quantize(satoshi), money.currency)

    def __init__(self, raw: List[Union[float, Decimal]], market: 'Market', ask_bid: str, limit_order_price: Union[Money,float,int,str,Decimal]=None):
        self.market           = market
        self.ask_bid          = ask_bid
        self.base_currency    = market['base']
        self.quote_currency   = market['quote']
        self.exchange_name    = market['exchange']

        self.raw              = raw
        self.quote_unit_price = Money(Decimal(raw[0]).quantize(satoshi), self.quote_currency)
        self.base_volume      = Money(Decimal(raw[1]).quantize(satoshi), self.base_currency)
        if not limit_order_price:
            self.limit_order_price = self.quote_unit_price # used for combined orders
            self.is_combined       = False
        else:
            if not isinstance(limit_order_price, Money):
                limit_order_price = self.quantize(Money(limit_order_price, self.quote_currency))
            assert limit_order_price.currency == self.quote_currency
            self.limit_order_price = limit_order_price
            self.is_combined       = True


    @property
    def base_unit_price(self) -> Money:
        """ price of 1 unit BTC in MOON """
        amount = 1 / self.quote_unit_price.amount
        return Money( Decimal(amount).quantize(satoshi), self.base_currency)

    @property
    def base_total_price(self) -> Money:
        """ price of volume in MOON - same as base_volume  """
        return self.base_volume

    # @property
    # def base_volume(self):
    #     """ total amount of order in MOON """
    #     return self.raw[1]

    # @property
    # def quote_unit_price(self):
    #     """ price of 1 unit MOON in BTC """
    #     return self.raw[0]

    @property
    def quote_total_price(self) -> Money:
        """ price of 1 unit BTC in MOON - same as quote_volume """
        return self.quote_volume

    @property
    def quote_volume(self) -> Money:
        """ total amount of order in BTC """
        quote_volume = Money(self.base_volume.amount / self.base_unit_price.amount, self.quote_currency)
        return self.quantize(quote_volume)

    @quote_volume.setter
    def quote_volume(self, quote_volume: Money):
        assert quote_volume.currency == self.quote_currency

        base_volume = Money(quote_volume.amount / self.quote_unit_price.amount, self.base_currency)
        self.base_volume = self.quantize(base_volume)


    def __gt__(self, other: 'Order'):
        assert self.base_currency    == other.base_currency
        assert self.quote_currency   == other.quote_currency
        assert self.base_unit_price  == other.base_unit_price
        assert self.quote_unit_price == other.quote_unit_price

        return self.quote_total_price > other.quote_total_price


    def __eq__(self, other):
        fields = [
            "quote_unit_price", "base_volume", "limit_order_price",
            "base_currency", "quote_currency",
            "market", "ask_bid",  "exchange_name"
        ]
        for key in fields:
            if getattr(self, key) != getattr(other, key):
                return False
        return True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.ask_bid == "bid":  # base -> quote
            """bluetrade(ask): 1000000 MOON -> 0.01 BTC @ 1e-08 MOON/BTC"""
            return "%s(%s): %s -> %s @ %.8f %s/%s, avg: %.8f" % (
                self.exchange_name, self.ask_bid,
                str(self.base_total_price),
                str(self.quote_total_price),
                self.limit_order_price.amount, self.base_currency, self.quote_currency,
                self.quote_unit_price.amount
            )
        if self.ask_bid == "ask":  # quote -> base
            """ bluetrade(bid): 0.02 BTC -> 1000000 MOON @ 2e-08 MOON/BTC"""
            return "%s(%s): %s -> %s @ %.8f %s/%s, avg: %.8f" % (
                self.exchange_name, self.ask_bid,
                str(self.quote_total_price),
                str(self.base_total_price),
                self.limit_order_price.amount, self.base_currency, self.quote_currency,
                self.quote_unit_price.amount
            )

