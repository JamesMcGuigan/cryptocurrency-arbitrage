import asyncio
import time

from money import Money
from pydash import py_ as _

from .exchange import Exchange


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()


async def main_async():
    # exchange_names = ccxt.exchanges
    exchange_names   = [ "bleutrade", "kraken", "bittrex", "nova", "poloniex", "yobit" ]
    arbitrage_coins  = [ Money(100000, "MOON"), Money(0.01, "BTC"), Money(0.1, "ETH"), Money(1000, "DOGE") ]
    # exchange_names   = [ "bleutrade" ]
    # arbitrage_coins  = [ Money(100000, "MOON") ]

    exchanges = {}
    for exchange_name in exchange_names:
        attempts_remaining = 10
        while not exchange_name in exchanges and attempts_remaining >= 0:
            attempts_remaining -= 1
            try:
                print("loading: %s" % exchange_name)
                # exchanges[exchange_name] = Exchange.init_sync(exchange_name, limit=None)
                exchanges[exchange_name] = await Exchange.init_async(exchange_name, limit=None)
                pass
            except: time.sleep(1)

    arbitrage_markets = {}
    for exchange_name in exchange_names:
        for input_coin in arbitrage_coins:
            print("find_arbitrage_loops: %s -> %s" % (exchange_name, input_coin))
            arbitrage_markets[exchange_name+':'+str(input_coin)] = exchanges[exchange_name].find_arbitrage_loops(input_coin)

    for key, arbitrage_loops in arbitrage_markets.items():
        print("%s : %s loops" % (key, len(arbitrage_loops)))
        print("==============================")
        for trade in _.take(arbitrage_loops, 10):
            print("--------------------")
            print(key, " -> ", trade.amount, trade.currency)
            for history_item in trade.history:
                print(history_item)
            print("\n")
        print("\n\n\n")
    print("==============================")
    print("DONE")


if __name__ == "__main__":
    main()