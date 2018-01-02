Cryptocurrency Arbitrage
========================

This is a python3 framework for detecting arbitrage trading opportunities on the 
various markets supported by ccxt.

It starts by downloading order books for all markets from all exchanges.
 
`Exchange.find_arbitrage_loops()` is then provided with a starting `Money(0.01, 'BTC')` coin, 
for which it will perform a market paper-trade on each valid market to produce a list 
of possible output coins. Each of these will then be traded again on each market, 
up to a specified depth of trades, until a loop is found where the output is of 
the same currency as the original trade. Trades are sorted by profit and only those matching
minimum profit ratio are returned.

The trading calculation takes into account the market depth from the order books as well as 
trading fees and minimum order values. 

Arbitrage opportunities within a single exchange are rare, so a profit setting of 0.9 
may be required to show actual output

 
Future
------

There are currently no command line flags for options, so you have to edit 
`./arbitrage/main.py` directly to set the options

Arbitrage loops are currently only searched for within a single exchange, 
but there is a plan to refactor this codebase to detect multi-exchange arbitrage opportunities
 
Loading data from exchanges is partially serialized and could be improved with better asyncio code

Code execution is currently fairly slow especially for the combinatorial explosion of 
possible trades at arbitrage depths greater than 4. This is a CPU bound task.
Implementing `pathos.multithreading.ProcessPool()` would allow python to use all available CPUs 
and not just a single core. 
     

Installation
------------

```
./requirements.sh
source venv/bin/activate

time python3 -u arbitrage.py 2>&1 | tee arbitrage.output.txt
```

Mooncoin Market Analysis
------------------------

There is also a juypter notebook containing some basic analysis of the Bleutrade Mooncoin market 
in `./mooncoin/mooncoin.ipynb` 

```
./requirements.sh
source venv/bin/activate

./jupyter_start.sh
./jupyter_stop.sh
``` 