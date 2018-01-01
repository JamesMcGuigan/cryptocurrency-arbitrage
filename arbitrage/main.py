import asyncio

from .exchange import Exchange


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async())
    loop.close()

async def main_async():
    exchanges = {}
    # exchange_names = ccxt.exchanges
    exchange_names = [ "bleutrade" ]
    for exchange_name in exchange_names:
        # exchanges[exchange_name] = Exchange.init_sync(exchange_name, limit=5)
        exchanges[exchange_name] = await Exchange.init_async(exchange_name, limit=5)
        print(exchanges[exchange_name].markets)


if __name__ == "__main__":
    main()