
from typing import Union

from money import Money

from .trade import Trade


class Market(dict):
    """
    {
        'ADC/BTC': {
            'active': 'true',
            'base': 'ADC',
            'id': 'ADC_BTC',
            'info': {
                'BaseCurrency': 'BTC',
                'BaseCurrencyLong': 'Bitcoin',
                'IsActive': 'true',
                'MarketCurrency': 'ADC',
                'MarketCurrencyLong': 'Audiocoin',
                'MarketName': 'ADC_BTC',
                'MinTradeSize': '0.00001000'
            },
            'limits': {
                'amount': {'max': None, 'min': '0.00001000'},
                'cost': {'max': None, 'min': 0},
                'price': {'max': None, 'min': None}
            },
            'lot': 1e-08,
            'maker': 0.0025,
            'percentage': True,
            'precision': {'amount': 8, 'price': 8},
            'quote': 'BTC',
            'symbol': 'ADC/BTC',
            'taker': 0.0025,
            'tierBased': False
            'bids': [ [3.3e-07, 249411.40730615], [3.2e-07, 152641.92140463], ... ],  # rate, volume
            'asks': [ [3.4e-07, 70970.70632278],  [3.5e-07, 74728.63434913],  ... ],  # rate, volume
            'timestamp': 1514753486330,
            'datetime': '2017-12-31T20:51:26.330Z'
            'exchange': 'bleutrade'
        },
    }
    """
    def __init__(self, *args):
        dict.__init__(self, *args)

    def trade(self, coin: Union[Money, Trade]) -> Trade:
        if coin.currency == self['base']:
            pass
        elif coin.currency == self['quote']:
            pass
        else:
            return Trade(
                input=coin,
                output=Money(0, "Invalid"),
                market=self
            )

    def price(self, coin: Money) -> Money:
        return self.trade(coin).output

