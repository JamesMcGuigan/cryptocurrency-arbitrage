import asyncio
import re

import money
from money import Money

from .exchange import Exchange

money.REGEX_CURRENCY_CODE = re.compile("^[A-Z]{4}$")


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()

async def main_async():
    exchanges = {}
    arbitrage_loops = {}
    # exchange_names = ccxt.exchanges
    exchange_names = [ "bleutrade" ]
    for exchange_name in exchange_names:
        exchanges[exchange_name] = Exchange.init_sync(exchange_name, limit=None)
        # exchanges[exchange_name] = await Exchange.init_async(exchange_name, limit=None)

    for exchange_name in exchange_names:
        arbitrage_loops[exchange_name] = exchanges[exchange_name].find_arbitrage_loops(Money(1000000, "MOON"))

        for i, arbitrage_loop in enumerate(arbitrage_loops):
            print("----------------------------------------")
            print("arbitrage_loop: %s - %s" % (i, exchange_name))
            print(arbitrage_loop)
            print("\n\n\n")

if __name__ == "__main__":
    main()