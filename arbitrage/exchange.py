import asyncio
import re
import time
from decimal import Decimal
from typing import Union, List

import ccxt
import ccxt.async as ccxt_async
import pandas as pd
from money import Money
from pydash import py_ as _

from .market import Market
from .trade import Trade


class Exchange():
    cache = {}

    @classmethod
    async def init_async(cls, name: str, reload: bool=False, limit: int=None):
        if name not in cls.cache or reload:
            is_async = True
            exchange     = getattr(ccxt_async, name)({ "timeout": 30*1000 })
            markets      = await exchange.fetch_markets()
            markets      = _(markets[:limit]).filter({ 'active': 'true' }).key_by('symbol').value()
            symbols      = sorted(markets.keys())
            order_books  = await asyncio.gather(*[ exchange.fetch_order_book(symbol) for symbol in symbols ])
            order_books  = dict(_.zip(symbols, order_books))

            cls.cache[name] = Exchange(name, exchange, markets, order_books, is_async)

        return cls.cache[name]

    @classmethod
    def init_sync(cls, name: str, reload: bool=False, limit: int=None):
        if name not in cls.cache and not reload:
            is_async = False
            exchange = getattr(ccxt, name)({ "timeout": 30*1000 }) # timeout 100s - occasionally causes timeout errors
            markets  = exchange.fetch_markets()
            markets  = _(markets[:limit]).filter({ 'active': 'true' }).key_by('symbol').value()
            symbols  = sorted(markets.keys())

            # order_books = { symbol: exchange.fetch_order_book(symbol) for symbol in symbols }
            order_books = {}
            for symbol in symbols:
                while not order_books.get(symbol):
                    try:    order_books[symbol] = exchange.fetch_order_book(symbol)
                    except: time.sleep(1)  # occasionally an order book will time out, so keep trying until it succeeds

            cls.cache[name] = Exchange(name, exchange, markets, order_books, is_async)

        return cls.cache[name]


    def __init__(self, name: str, exchange: ccxt.Exchange, markets: dict, order_books: dict, is_async: bool=False):
        self.is_async = is_async
        self.name     = name
        self.exchange = exchange

        # self.symbols = ['ADC/BTC', 'ADC/DOGE', 'ADC/ETH', 'BCH/BTC', 'BCH/DOGE', 'BCH/ETH', 'BITB/BTC', 'BITB/DOGE', 'BITB/ETH', 'BLK/BTC', 'BLK/DOGE', 'BLK/ETH', ... ]
        self.symbols    = sorted(markets.keys())

        # self.currencies = ['ADC', 'BCH', 'BITB', 'BLK', 'BSTY', ]
        self.currencies = _(exchange.symbols).map(lambda s: re.split('/', s)).flatten().uniq().sort_by().value()

        for symbol in self.symbols:
            markets[symbol]['exchange'] = name
            _.assign(markets[symbol], order_books[symbol])
            markets[symbol] = Market(markets[symbol])

        self.markets        = markets
        self.markets_df     = pd.DataFrame(markets)


    def find_arbitrage_loops(self, input_coin: Union[Money, Trade], depth: int=4, profit=1.0) -> List[Trade]:
        trades_inprogress = [input_coin]
        trades_completed  = []
        for i in range(depth):
            trades_returned    = self.trade_all_markets(trades_inprogress)
            trades_completed  += [ trade for trade in trades_returned if trade.output.currency == input_coin.currency ]
            trades_inprogress  = [ trade for trade in trades_returned if trade.output.currency != input_coin.currency ]

        trades_completed  = list(reversed(sorted(trades_completed, key=lambda t: t.amount)))
        trades_profitable = [ trade for trade in trades_completed if trade.output > (input_coin * Decimal(profit)) ]
        return trades_profitable


    def trade_all_markets(self, inputs: List[Union[Money, Trade]]) -> List[Trade]:
        if not isinstance(inputs, list): inputs = [inputs]

        trades = []
        for input in inputs:
            available_markets = _.pick_by(self.markets, lambda market, name: market.can_trade(input))
            for name, market in available_markets.items():
                trade = market.trade(input)
                trades += [ trade ]

        return trades

