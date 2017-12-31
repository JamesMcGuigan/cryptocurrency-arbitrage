#!/usr/bin/env python3

import asyncio
from collections import OrderedDict
from copy import deepcopy
from decimal import Decimal
from typing import Union

import aiohttp
import requests
import simplejson
from pydash import py_ as _


class VolumeException(Exception):
    # noinspection PyArgumentList
    def __init__(self,*args,**kwargs):
        Exception.__init__(self,*args,**kwargs)


class BleuTrade:
    urls = {
        "base": "https://bleutrade.com/api/v2/public/",
        "order_book": "https://bleutrade.com/api/v2/public/getorderbook?market=%s&type=ALL&depth=1000",
        "market": "https://bleutrade.com/api/v2/public/getmarkets",
        "history": "https://bleutrade.com/api/v2/public/getorderbook?market=%s&count=200",
    }

    def __init__(self):
        pass

    @classmethod
    def fetch_sync(cls, url):
        response = requests.get(url)
        response_json = simplejson.loads(response.text)['result']
        return response_json

    @classmethod
    async def fetch_async(cls, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                text = await response.text()
                response_json = simplejson.loads(text)['result']
                return response_json


class Market(BleuTrade):
    def __init__(self, market_name, markets_json, order_book_json):
        super().__init__()
        self.market_name = market_name
        self.market      = next(market for market in markets_json if market['MarketName'] == market_name)
        self.order_book  = self.convert_order_book_to_decimal(order_book_json)

    @classmethod
    async def init_async(cls, market_name):
        market_json     = await BleuTrade.fetch_async(cls.urls['market'])
        order_book_json = await BleuTrade.fetch_async(cls.urls['order_book'] % market_name)
        history         = await BleuTrade.fetch_async(cls.urls['history']    % market_name)
        self = Market(market_name, market_json, order_book_json)
        return self

    @classmethod
    def convert_order_book_to_decimal(cls, order_book):
        """
        order_book = {
            "buy":  [{'Quantity': '458888746.11665452',  'Rate': '0.00000001'}],
            "sell": [[{'Quantity': '2304237552.2191453', 'Rate': '0.00000002'}],
        }
        :param order_book: json dict from api fetch
        :type  order_book: dict
        :return: order_book with all number strings converted to Decimal
        :rtype:  dict
        """
        for buy_sell, order_items in order_book.items():
            for i, order in enumerate(order_items):
                for key, value in order.items():
                    order_book[buy_sell][i][key] = Decimal(value)

        order_book["buy"]  = sorted(order_book["buy"], key=lambda d: -d['Rate'])
        order_book["sell"] = sorted(order_book["sell"], key=lambda d: d['Rate'])
        return order_book

    def price(self, buy_sell: str, volume: Union[int,float,Decimal]=0) -> Decimal:
        """

        :param buy_sell:  ["buy", "sell", "mid"]
        :param volume:    units to buy in the MarketCurrency ie for MOON_BTC this would be MOON
        :return:          price in BaseCurrency
        """
        assert buy_sell in ["buy", "sell", "mid"]

        if buy_sell == "mid":
            return (self.order_book["sell"][0]["Rate"] + self.order_book["buy"][0]["Rate"]) / 2
        else:
            if volume == 0:
                return self.order_book[buy_sell][0]["Rate"]
            else:
                queue     = self.order_book[buy_sell]
                orders    = []
                remaining = volume

                # Pick out all the orders required to fulfil the volume
                for order in queue:
                    order = deepcopy(order)
                    if order['Quantity'] > remaining:
                        order['Quantity'] = Decimal(remaining)
                    orders.append(order)
                    remaining -= order['Quantity']
                    if remaining == 0:
                        break

                price = Decimal(0)
                for order in orders:
                    price += order['Quantity'] * order['Rate']

                if remaining > 0:
                    raise VolumeException("%s: price(%s) -> price: %s, volume: %s, remaining: %s, orders: %s" % (self.market_name, buy_sell, price, volume, remaining, orders))

                return price

    def mid_market_value(self):
        return self.price("mid", 0)


async def main():
    market_names     = [ "MOON_BTC", "MOON_DOGE", "MOON_ETH", "DOGE_BTC", "ETH_BTC" ]
    # market_objects   = await paco.map(Market.init_async, market_names)
    market_objects   = await asyncio.gather(*[ Market.init_async(market_name) for market_name in market_names ])
    markets          = OrderedDict(_.zip(market_names, market_objects))

    for market_name, market in markets.items():
        print(market_name, "\tbuy: %-11s\tmid: %-11s\tsell: %-11s\t" % tuple([ market.price(type) for type in ["buy", "mid", "sell"] ]))



if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
