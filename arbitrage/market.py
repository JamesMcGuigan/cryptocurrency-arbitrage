from decimal import Decimal
from typing import Union

from money import Money

from arbitrage.order import Order
from arbitrage.trade import Trade


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

