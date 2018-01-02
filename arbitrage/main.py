import asyncio

import ccxt
from money import Money

from .exchange import Exchange


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()


async def main_async():
    exchange_names = ccxt.exchanges
    # exchange_names   = [ "bleutrade", "kraken", "bittrex", "nova", "poloniex", "yobit" ]
    arbitrage_coins  = [
        Money(0.01,      "BTC"),
        Money(0.1,       "ETH"),
        Money(100000,    "MOON"),
        Money(10000,     "DOGE"),
    ]

    exchanges = {}
    for exchange_name in exchange_names:
        attempts_remaining = 6
        print("loading: %s " % exchange_name, end='')
        while not exchange_name in exchanges and attempts_remaining >= 0:
            attempts_remaining -= 1
            try:
                # exchanges[exchange_name] = Exchange.init_sync(exchange_name, limit=None)
                exchanges[exchange_name] = await Exchange.init_async(exchange_name, limit=None)
            except:
                print(".", end='')
        print("")

    arbitrage_markets = {}
    for exchange_name in exchanges.keys():
        for input_coin in arbitrage_coins:
            print("find_arbitrage_loops: %s -> %s" % (exchange_name, input_coin))
            arbitrage_markets[exchange_name+':'+str(input_coin)] = exchanges[exchange_name].find_arbitrage_loops(input_coin, depth=4, profit=1)

    for key, arbitrage_loops in arbitrage_markets.items():
        if len(arbitrage_loops):
            print("\n----------------------------------------\n".join([ trade for trade in arbitrage_loops ]))
    print("DONE")


if __name__ == "__main__":
    main()