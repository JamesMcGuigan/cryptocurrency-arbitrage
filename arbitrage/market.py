
from copy import deepcopy
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

        output = deepcopy(self)
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

        output = deepcopy(self)
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




class Trade():
    def __init__(self, input: Money, output: Money, market: 'Market', orders: List[Order]=None, previous_trade: 'Trade'=None):
        self.input  = input
        self.output = output
        self.market = market
        self.orders = orders
        if previous_trade: self.history = _([previous_trade.history, self]).flatten_deep().filter().uniq().value()
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
        combined_order = Order.combined(self.orders)
        return combined_order.__str__()


class Market(dict):
    """
    {
      'tierBased': False,
      'percentage': True,
      'maker': 0.0025,
      'taker': 0.0025,
      'id': 'MOON_BTC',
      'symbol': 'MOON/BTC',
      'base': 'MOON',
      'quote': 'BTC',
      'active': 'true',
      'info': {
        'MarketCurrency': 'MOON',
        'BaseCurrency': 'BTC',
        'MarketCurrencyLong': 'Mooncoin',
        'BaseCurrencyLong': 'Bitcoin',
        'MinTradeSize': '0.00001000',
        'MarketName': 'MOON_BTC',
        'IsActive': 'true'
      },
      'lot': 1e-08,
      'precision': { 'amount': 8, 'price': 8 },
      'limits': {
        'amount': { 'min': '0.00001000', 'max': None },
        'price':  { 'min': None,         'max': None },
        'cost':   { 'min': 0,            'max': None }
      },
      'exchange': 'bleutrade',
      'bids': [[ 1e-08, 1403365903.5051105 ] ],
      'asks': [[ 2e-08, 784728084.2246515 ], [ 3e-08, 1107880502.633399 ], ... ]
      'timestamp': 1514818799398,
      'datetime': '2018-01-01T14:59:59.398Z'
    }
    """
    def __init__(self, *args):
        dict.__init__(self, *args)

    def can_trade(self, coin: Money) -> bool:
        return coin.currency in [ self['base'], self['quote']]

    def trade(self, input_coin: Union[Money, Trade]) -> Trade:
        previous_trade = None
        if isinstance(input_coin, Trade):
            previous_trade = input_coin
            input_coin = previous_trade.output

        remaining            = Money(input_coin.amount, input_coin.currency)
        minimum_order_amount = Money(self['limits']['amount']['min'], self['quote'])

        orders = []
        output_coin = Money(0, 'XXX')
        if remaining.currency == self['base']:
            output_coin = Money(0, self['quote'])
            for order in self['bids']:
                order         = Order(order, self, 'bid')  # MOON base -> quote BTC
                order         = order.with_max_remaining(remaining)
                minimum_order = order.get_minimum_order(minimum_order_amount)

                if remaining > minimum_order.base_total_price:
                    output_coin += order.quote_total_price
                    remaining   -= order.base_total_price
                    orders      += [ order ]
                else: break

        elif remaining.currency == self['quote']:
            output_coin = Money(0, self['base'])
            for order in self['asks']:
                order         = Order(order, self, 'ask')  # BTC quote -> base MOON
                order         = order.with_max_remaining(remaining)
                minimum_order = order.get_minimum_order(minimum_order_amount)

                if remaining > minimum_order.quote_total_price:
                    output_coin += order.base_total_price
                    remaining   -= order.quote_total_price
                    orders      += [ order ]
                else: break

        output_coin *= (1 - Decimal(self['taker']))
        output_coin = Order.quantize(output_coin)

        return Trade(
            input=input_coin,
            output=output_coin,
            market=self,
            orders=orders,
            previous_trade=previous_trade
        )

    def price(self, coin: Money) -> Money:
        return self.trade(coin).output

