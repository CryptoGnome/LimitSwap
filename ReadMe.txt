Hello, Welcome to LimitSwap!

LimitSwap is a Defi Trading Bot the currently works on mutliple EVM chains.
The setup process is quick but be sure to read all of the documents listed beliw to help you get started.

Detailed Wiki & Guides Here: https://limitswapv3.gitbook.io/limitswap/

--------------------------------------------------------------------------------
HOW TO CONFIGURE THE BOT
--------------------------------------------------------------------------------

1/ settings.json

On the EXCHANGE field, just put the exchange you want to use. Available values:
- Uniswap
- Pancakeswap
- Spiritswap
- Spookyswap
- Quickswap


--------------------------------------------------------------------------------

2/ tokens.json

- SYMBOL : symbol of the token you want to buy

- ADDRESS : contract address of the token you want to buy

- USECUSTOMBASEPAIR : must be "true" or "false"
     - "false" : the bot uses BNB / ETH  to make trades --> you only need to hold BNB or ETH
     - "true" : bot uses the BASE pair you've entered below

- BASESYMBOL : symbol of the token you want to trade with ***** if you selected USECUSTOMBASEPAIR = True *****

- BASEADDRESS : contract address of the token you want to trade with ***** if you selected USECUSTOMBASEPAIR = True *****

- BUYAMOUNTINBASE : put here the amount in the base symbol that you want the bot to buy

- BUYPRICEINBASE : buy price of 1 token in the base symbol
    if the price of 1 token is < or = to this price, the bot will buy.

- SELLAMOUNTINTOKENS : put here the amount of token that you want the bot to sell

- SELLPRICEINBASE : sell price of 1 token in the base symbol :
    if the price of 1 token is > or = to this price, the bot will sell.

- MAXTOKENS :
    - before buying, the bot checks MAXTOKENS
    - if you hold more tokens than MAXTOKENS, the bot does not buy
    (but even if you set MAXTOKENS = 1, the bot can buy 50000 tokens for example, no problem)
    
    Tip : MAXTOKENS is often used to make the bot stop buying after 1 trade : simply set it to a low value, like "1", if you want to do that.

- MOONBAG : minimal amount of token you want to keep in your wallet. If you don't want to keep any token, put 0.

- SLIPPAGE : slippage you want to use

- HASFEES : select "TRUE" if you want to trade a token with additional fees, like automatic transfer to liquidity when you buy / additional taxes / rebase / etc.

- GAS / BOOSTPERCENT :
  There is 2 ways to set your Gas    *****ONLY FOR ETH*****
     1/ Set your own fixed Gas price --> simply set Gas price in "GAS" parameter
        example : "GAS": "200",
     2/ Let the bot calculate Gas price relating to current Gas Price on blockchain :
           - it reads the gas price on https://ethgasstation.info/
           - it applies the boost you set on Fast price
        example : "GAS": "BOOST",  "BOOSTPERCENT": "50",

- GASLIMIT : always used, set it with the value you want to use.

- LIQUIDITYCHECK : option for snipe at listings.
    - If you select "true", the bots check if liquidity is added before buying
    - If you select "false", bot is faster, but don't check liquidity

- LIQUIDITYAMOUNT : minimal amount of liquidity (in BNB/ETH/FTM...) before bot buys

--------------------------------------------------------------------------------


Enjoy our bot!
LimitSwap Team



