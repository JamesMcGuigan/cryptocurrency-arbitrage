
from decimal import Decimal
from typing import Union, List

from money import Money
from pydash import py_ as _

satoshi = Decimal('0.00000001')

class Order():
    @classmethod
    def combined(cls, orders: 'List[Order]') -> 'Order':
        assert _(orders).map(lambda o: o.base_currency).uniq().size().value()      == 1
        assert _(orders).map(lambda o: o.quote_currency).uniq().size().value()     == 1
        assert _(orders).map(lambda o: o.ask_bid).uniq().size().value()            == 1
        assert _(orders).map(lambda o: o.market['symbol']).uniq().size().value()   == 1
        assert _(orders).map(lambda o: o.market['exchange']).uniq().size().value() == 1

        base_volume    = 0
        base_price_sum = 0
        for order in orders:
            base_volume    += order.base_volume
            base_price_sum += order.base_price_unit * order.base_volume
        base_price_avg = base_price_sum / base_volume
        combined_order = Order([base_price_avg, base_volume], orders[0].market, orders[0].ask_bid)
        return combined_order


    def __init__(self, raw: List[Union[float, Decimal]], market: 'Market', ask_bid: str):
        self.raw              = [Decimal(value).quantize(satoshi) for value in raw]
        self.quote_price_unit = self.raw[0]
        self.base_volume      = self.raw[1]

        self.market         = market
        self.ask_bid        = ask_bid
        self.base_currency  = market['base']
        self.quote_currency = market['quote']
        self.exchange_name  = market['exchange']

    @property
    def base_price_unit(self):
        """ price of 1 unit BTC in MOON """
        return Decimal(1 / self.quote_price_unit).quantize(satoshi)

    # @property
    # def base_volume(self):
    #     """ total amount of order in MOON """
    #     return self.raw[1]

    # @property
    # def quote_price_unit(self):
    #     """ price of 1 unit MOON in BTC """
    #     return self.raw[0]

    @property
    def quote_volume(self):
        """ total amount of order in BTC """
        return Decimal(self.base_volume / self.base_price_unit).quantize(satoshi)


    def set_max_remaining(self, remaining: Money):
        """
        If remaining money is insufficient to fufill total volume, reduce order size to
        :param remaining:
        :return:
        """
        if remaining.currency == self.base_currency:
            if remaining.amount < self.base_volume:
                self.base_volume = remaining.amount
        if remaining.currency == self.quote_currency:
            if remaining.amount < self.quote_volume:
                self.base_volume = remaining.amount * self.quote_price_unit

        self.base_volume = Decimal(self.base_volume).quantize(satoshi)
        self.raw[1]      = self.base_volume


    def __eq__(self, other):
        for key in ["quote_price_unit", "base_volume", "market", "ask_bid", "base_currency", "quote_currency", "exchange_name"]:
            if getattr(self, key) != getattr(other, key):
                return False
        return True

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.ask_bid == "bid":  # base -> quote
            """ ask: 1000000 MOON -> 0.01 BTC @ 1e-08 MOON/BTC | bluetrade"""
            return "%s: %s %s -> %s %s @ %.8f %s/%s | %s" % (
                self.ask_bid,
                self.base_volume, self.base_currency,
                self.quote_volume, self.quote_currency,
                self.base_price_unit, self.base_currency, self.quote_currency,
                self.exchange_name
            )
        if self.ask_bid == "ask":  # quote -> base
            """ bid: 0.02 BTC -> 1000000 MOON @ 2e-08 MOON/BTC | bluetrade"""
            return "%s: %s %s -> %s %s @ %.8f %s/%s | %s" % (
                self.ask_bid,
                self.quote_volume, self.quote_currency,
                self.base_volume, self.base_currency,
                self.base_price_unit, self.base_currency, self.quote_currency,
                self.exchange_name
            )



class Trade():
    def __init__(self, input: Money, output: Money, market: 'Market', orders: List[Order]=None, previous_trade: 'Trade'=None):
        self.input  = input
        self.output = output
        self.market = market
        self.orders = orders
        if previous_trade: self.history = _([previous_trade, previous_trade.history]).flatten().uniq().value()
        else:              self.history = []


    @property
    def amount(self):
        """ Duck type Money """
        return self.output.amount


    @property
    def currency(self):
        """ Duck type Money """
        return self.output.currency

    def __eq__(self, other):
        for key in ["input", "output", "market", "orders"]:  # ignores history
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
        if args[0]['id'] == "MOON_BTC": print(args[0])
        dict.__init__(self, *args)

    def can_trade(self, coin: Money) -> bool:
        return coin.currency in [ self['base'], self['quote']]

    def trade(self, input_coin: Union[Money, Trade]) -> Trade:
        previous_trade = None
        if isinstance(input_coin, Trade):
            previous_trade = input_coin
            input_coin = previous_trade.output

        remaining = Money(input_coin.amount, input_coin.currency)
        orders = []
        output_coin = Money(0, 'XXX')
        if remaining.currency == self['base']:
            output_coin = Money(0, self['quote'])
            for order in self['bids']:
                order = Order(order, self, 'bid')  # base -> quote
                order.set_max_remaining(remaining)
                if remaining.amount > 0 and order.quote_volume >= Decimal(self['limits']['amount']['min']):
                    output_coin = Money(output_coin.amount + order.quote_volume, output_coin.currency)
                    remaining   = Money(remaining.amount   - order.base_volume,  remaining.currency)
                    orders     += [ order ]
                else: break
                if remaining.amount == 0: break

        elif remaining.currency == self['quote']:
            output_coin = Money(0, self['base'])
            for order in self['asks']:
                order = Order(order, self, 'ask')  # quote -> base
                order.set_max_remaining(remaining)
                if remaining.amount > 0 and order.quote_volume >= Decimal(self['limits']['amount']['min']):
                    output_coin = Money(output_coin.amount + order.base_volume,  output_coin.currency)
                    remaining   = Money(remaining.amount   - order.quote_volume, remaining.currency)
                    orders     += [order]
                else: break
                if remaining.amount == 0: break

        output_coin_amount = Decimal(output_coin.amount * (1 - Decimal(self['taker']))).quantize(satoshi)
        output_coin = Money(output_coin_amount,  output_coin.currency)
        return Trade(
            input=input_coin,
            output=output_coin,
            market=self,
            orders=orders,
            previous_trade=previous_trade
        )

    def price(self, coin: Money) -> Money:
        return self.trade(coin).output

