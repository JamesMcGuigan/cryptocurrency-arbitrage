import asyncio

from money import Money
from pydash import py_ as _

from .exchange import Exchange


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()


async def main_async():
    # exchange_names = ccxt.exchanges
    exchange_names   = [ "bleutrade" ]
    arbitrage_coins  = [ Money(1000000, "MOON"), Money(0.01, "BTC") ]

    exchanges = {}
    for exchange_name in exchange_names:
        exchanges[exchange_name] = Exchange.init_sync(exchange_name, limit=None)
        # exchanges[exchange_name] = await Exchange.init_async(exchange_name, limit=None)

    arbitrage_markets = {}
    for exchange_name in exchange_names:
        for input_coin in arbitrage_coins:
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


if __name__ == "__main__":
    main()