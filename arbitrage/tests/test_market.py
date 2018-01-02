import pytest
from money import Money
from pydash import py_ as _

from ..market import Market
from ..order import Order

markets_json = {
    "MOON/BTC":  {
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
        'asks': [[ 2e-08, 784728084.2246515 ], [ 3e-08, 1107880502.633399 ] ],
        'timestamp': 1514818799398,
        'datetime': '2018-01-01T14:59:59.398Z'
    }
}
markets = _.map_values(markets_json, Market)

@pytest.mark.parametrize("test", [
    {
        "notes":  "minimum order value",
        "market": "MOON/BTC",
        "input":  Money(1, "MOON"),
        "output": Money(0, "BTC"),
        "orders": []
    },
    {
        "notes":  "bid price",
        "market": "MOON/BTC",
        "input":  Money('100000000', "MOON"),
        "output": Money('0.9975000', "BTC"),
        "orders": [
            Order([ 1e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='bid')
        ]
    },
    {
        "notes":  "bid price",
        "market": "MOON/BTC",
        "input":  Money('2',        "BTC"),
        "output": Money('99750000', "MOON"),
        "orders": [
            Order([ 2e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='ask')
        ]
    }
])
def test_trade(test):
    trade = markets[test['market']].trade(test['input'])
    assert trade.market == markets[test['market']]
    assert trade.output == test['output']
    assert trade.orders == test['orders']
    pass


@pytest.mark.parametrize("test", [
    {
        "notes":   "basic getter and setter calculations",
        "market":  "MOON/BTC",
        "ask_bid": "ask",
        "input":   [ 1e-08, 100000000 ],
        "output": {
            "base_unit_price":   Money('100000000', 'MOON'),  # price of 1 unit BTC in MOON
            "base_total_price":  Money('100000000', 'MOON'),  # total amount of order in MOON
            "base_volume":       Money('100000000', 'MOON'),  # total amount of order in MOON
            "base_currency":     "MOON",
            "quote_unit_price":  Money('0.00000001', 'BTC'),  # price of 1 unit MOON in BTC
            "quote_total_price": Money('1', 'BTC'),           # total amount of order in BTC
            "quote_volume":      Money('1', 'BTC'),           # total amount of order in BTC
            "quote_currency":    "BTC",
        }
    },
    {
        "notes":   "basic getter and setter calculations",
        "market":  "MOON/BTC",
        "ask_bid": "bid",
        "input":   [ 2e-08, 400000000 ],
        "output": {
            "base_unit_price":   Money( '50000000', 'MOON'),  # price of 1 unit BTC in MOON
            "base_total_price":  Money('400000000', 'MOON'),  # total amount of order in MOON
            "base_volume":       Money('400000000', 'MOON'),  # total amount of order in MOON
            "base_currency":     "MOON",
            "quote_unit_price":  Money('0.00000002', 'BTC'),  # price of 1 unit MOON in BTC
            "quote_total_price": Money('8', 'BTC'),           # total amount of order in BTC
            "quote_volume":      Money('8', 'BTC'),           # total amount of order in BTC
            "quote_currency":    "BTC",
        }
    }
])
def test_order(test):
    order = Order(test['input'], market=markets[test['market']], ask_bid=test['ask_bid'])
    input = { key: getattr(order,  key) for key in test['output'].keys() }
    assert input == test['output']


@pytest.mark.parametrize("test", [
    {
        "notes":  "test len() == 0",
        "input":  [],
        "output": None
    },
    {
        "notes":  "test len() == 1",
        "input":  [
            Order([ 1e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='ask')
        ],
        "output": Order([ 1e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='ask')
    },
    {
        "notes":  "ask len() == 2",
        "input":  [
            Order([ 1e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='ask'),
            Order([ 2e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='ask'),
            Order([ 3e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='ask')
        ],
        "output": Order([ 2e-08, 300000000 ], market=markets["MOON/BTC"], ask_bid='ask', limit_order_price=3e-08)
    },
    {
        "notes":  "ask len() == 2",
        "input":  [
            Order([ 3e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='bid'),
            Order([ 2e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='bid'),
            Order([ 1e-08, 100000000 ], market=markets["MOON/BTC"], ask_bid='bid')
        ],
        "output": Order([ 2e-08, 300000000 ], market=markets["MOON/BTC"], ask_bid='bid', limit_order_price=1e-08)
    },
])
def test_order_combined(test):
    combined_order = Order.combined(test['input'])
    assert combined_order == test['output']