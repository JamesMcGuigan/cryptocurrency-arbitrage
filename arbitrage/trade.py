from money import Money

class Trade():
    def __init__(self, input: Money, output: Money, market: 'Market', bids: list=None, asks: list=None, base_currency: str='BTC'):
        self.input  = input
        self.output = output
        self.market = market
        self.bids   = bids
        self.asks   = asks
        self.base_currency = base_currency
        pass

        # @property
        # def base_currency_value(self):
        #     Exchange[self.market['exchange']]
