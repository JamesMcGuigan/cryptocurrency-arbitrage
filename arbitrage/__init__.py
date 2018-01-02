import decimal

from .exchange import Exchange
from .main import main
from .main import main_async
from .market import Market
from .order import Order
from .trade import Trade

decimal.getcontext().prec = 100  # sometimes we encounter very large numbers
