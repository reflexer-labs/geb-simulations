
# Agent Catalog

## RAI Price Trader

### Description

The RAI price trader starts with a RAI and USD balance. It buys and sells RAI when RAI/USD is a certain percent deviation from Redemption Price. The percent deviation of each price trader is drawn from a normal distribution and stays constant over the agent's lifetime. Currently, each price trader starts with the same amount of capital.

### Parameters

1.  price_trader_count: number of price individual traders

2.  price_trader_mean_pct: mean of normal distribution from which price traders draw their percent deviations

3.  price_trader_min_pct: minimum percent deviation a price trader can have.  The standard deviation of the normal distribution is set to (price_trader_mean_pct - price_trader_min_pct)/2

### State Variables

1.  price_trader_list: stores all price trader states.  Each state is composed of:

1.  rai_balance

2.  usd_balance

3.  percent_bound: deviation used for entry/exit

### Inputs

1.  Uniswap RAI and ETH balances

2.  Redemption price

3.  Market price

### Outputs

1.  price_trader_list

2.  Uniswap RAI and ETH delta

### Pseudocode behavior

for each price trader in random order:

if market_price > redemption_price * (1 + percent_bound):

Sell RAI to peg or entire RAI balance

elif market_price < redemption_price * (1 - percent_bound):

Buy RAI to peg or entire USD balance

else

Do nothing


## RAI Rate Trader

### Description

The RAI rate trader starts with a RAI and USD balance. It buys/sells RAI when the magnitude of Redemption Rate is greater than a certain value and the market is below/above redemption price. The entry rate of each rate trader is drawn from a normal distribution and stays constant over the agent's lifetime. Currently, each rate trader starts with the same amount of capital.

### Parameters

1.  rate_trader_count: number of price individual traders

2.  rate_trader_mean_apy: mean of normal distribution from which rate traders draw their entry APYs

3.  rate_trader_min_apy: minimum entry APY a rate trader can have.  The standard deviation of the normal distribution is set to (rate_trader_mean_apy - rate_trader_min_apy)/2

### State Variables

1.  rate_trader_list: stores all rate trader states.  Each state is composed of:

1.  rai_balance

2.  usd_balance

3.  apy_bound: apy used for entry/exit

### Inputs

1.  Uniswap RAI and ETH balances

2.  Redemption price

3.  Market price

### Outputs

1.  rate_trader_list

2.  Uniswap RAI and ETH delta

### Pseudocode behavior

for each rate trader in random order:

if APY < -apy_bound and market_price > redemption_price:

Sell RAI to peg or entire RAI balance

elif APY > apy_bound and market_price < redemption_price:

Buy RAI to peg or entire USD balance

else

Do nothing


## Liquidity SAFEs

### Description

Each liquidity SAFE represents a SAFE owner that attempts to keep their SAFE at a specific collateralization ratio throughout ETH/USD fluctuations. Thus, the SAFE owner will exchange ETH for RAI on Uniswap and re-pay debt when ETH/USD goes down. Conversely, the SAFE owner will draw RAI and sell for ETH on Uniswap when ETH/USD goes up.

            Note: These agents do not carry an ETH balance. The ETH used to exchange ETH for RAI is unlimited and comes from outside the system.  The acquisition of this ETH does not affect the ETH/USD price 

### Parameters

### State Variables

1.  liquidity_cdp_rai_balance: total RAI held by liquidity SAFEs

2.  Liquidity_cdp_eth_collateral: total ETH locked by liquidity SAFEs

### Inputs

1.  cdps

2.  eth_price

3.  target_price

4.  liquidation_ratio

5.  liquidation_buffer

6.  RAI balance

7.  ETH balance

### Outputs

1.  cdps

2.  Uniswap RAI and ETH delta

Pseudocode behavior

for each liquidity cdp:

If not cdp_above_liquidation_buffer:

              wipe = wipe_to_liquidation_ratio * liquidation_buffer

                  swap ETH for wipe amount of RAI on uniswap

                  repay wipe amount of debt

elif cdp_above_liquidation_buffer:

draw = draw_to_liquidation_buffer

sell draw amount of RAI for ETH on uniswap

else:

Do nothing


## ETH Leverager

### Description

A DEFI saver kind of an agent: The agent leverages ETH with CDP and tries to maintain a collateral ratio that is between two values. The agent keeps all of its assets in the CDP and rebalances using flash loans.

### Parameters

1.  eth_leverager_target_min_liquidity_ratio: The min liquidation that the agent keeps. If the ratio dips lower, the agent rebalances to the average of min and max liq ratios

2.  eth_leverager_target_max_liquidity_ratio: The max liquidation that the agent keeps. If the ratio pumps higher, the agent rebalances to the average of min and max liq ratios

### State Variables

1.  CDPs The agent manages a CDP thats marked as "owner" = "leverager"

### Inputs

1.  Uniswap RAI and ETH balances

2.  Redemption price

3.  Market price

### Outputs

1.  Updated CDPs

2.  Uniswap RAI and ETH delta

### Pseudocode behavior

for each CDP that is owned by "leverager"

Preferred_ratio = (eth_leverager_target_min_liquidity_ratio + eth_leverager_target_max_liquidity_ratio)/2

If CDPs liquidity ratio is above eth_leverager_target_max_liquidity_ratio

Rebalance back to Preferred_ratio by buying from uniswap

If CDPs liquidity ratio is below eth_leverager_target_min_liquidity_ratio

Rebalance back to Preferred_ratio by buying from uniswap


## Malicious Whale Price Setter

### Description

The agent pumps or dumps the RAI market price and keeps it there for a while until the operation stops. The purpose of the agent is not to be profitable but just try to manipulate the price and see if the system can manage that.

### Parameters

1.  Malicious_whale_t0: the cumulative timestep time when whale starts to manipulate the price

2.  Malicious_whale_t1: the cumulative timestep time when whale stops

3.  Malicious_whale_pump_percent: if above 1, the amount how much to pump the price (1.05 would be 5% pump), if below, the amount how much the price gets dumped (0.95 would be dump by 5%)

4.  Malicious_whale_kp: The p value of controller that tries to maintain the price at the pumped value

### State Variables

1.  Malicious_whale_funds_eth: How much ETH the whale has in the beginning

2.  malicious_whale_funds_rai: How much RAI the whale has in the beginning

3.  malicious_whale_state: 0 if the whale has not started the pump and 1 if it has

4.  malicious_whale_p0:  Price of RAI just before the pump

### Inputs

1.  Uniswap RAI and ETH balances

2.  Redemption price

3.  Market price

### Outputs

1.  Malicious_whale_funds_eth

2.  Malicious_whale_funds_rai

3.  Malicious_whale_state

4.  malicious_whale_p0

5.  Uniswap RAI and ETH delta

### Pseudocode behavior

If cumulative_time > malicious_whale_t1 and cumulative_time < malicious_whale_t2

If malicious_whale_state == 0

Use 20% of all funds to dump/pump price to wanted direction

Calculate wanted_price as the current RAI price multiplied by Malicious_whale_pump_percent

else

diff = abs((wanted_price -market_price_twap)/market_price_twap/abs(1 - malicious_whale_pump_percent) * malicious_whale_kp)

If diff > 2

diff = 2

fraction_to_use =timedelta/(malicious_whale_t2 - malicious_whale_t1)*diff

if fraction_to_use < 0:

              fraction_to_use = 0

Set malicious_whale_state = 1

if market_price_twap < wanted_price:

buy RAI from uniswap with malicious_whale_funds_eth * fraction_to_use

if market_price_twap > wanted_price:

buy ETH from uniswap with malicious_whale_funds_rai * fraction_to_use

## Malicious RAI Trader with external funding

### Description

The agent is a p controller that trades RAI in to the opposite direction that the money god wants

### Parameters

1.  Malicious_rai_trader_max_balance:  The maximum amount of funds the trader can be long or short (in RAI)

2.  Malicious_rai_trader_p: The p controller value that controls how the trader trades

### State Variables

1.  Malicious_rai_trader_state: How much the trader is long/short at the moment (in RAI)

### Inputs

1.  Uniswap RAI and ETH delta

2.  Eth_price

3.  Market_price_twap

4.  target_price

### Outputs

1.  Malicious_rai_trader_state

2.  Uniswap RAI and ETH delta

### Pseudocode behavior

diff = market_price_twap-target_price)/market_price_twap*'malicious_rai_trader_p

if(diff>1):

diff = 1

if(diff<-1):

diff = -1

trade_interest = diff*malicious_rai_trader_max_balance

if(trade_interest > malicious_rai_trader_state):

Exchange RAI for ETH by trade_interest-malicious_rai_trader_state

elif(trade_interest < malicious_rai_trader_state):

Exchange ETH for RAI by malicious_rai_trader_state - trade_interest

## Money Market Agent

### Description

Money market consists of 3 agents with following strategies: 

#### RAI Lender
if lend_rate + RR > 0, buy RAI and loan it out, otherwise sell RAI

#### RAI Borrower
if RR < 0 and abs(RR) >= borrow rate, borrow RAI and sell, when not, repay and BUY

#### USD Rate Trader
if RR > external interest rate(USD), buy RAI, otherwise sell RAI for USD

These strategies are not followed exactly as the plan is to simulate that there are multiple players in the field and also the bigger the profit opportunity there is, the more capital should be abusing the rate.

This is simulated with linear relationship between the possible profit and max apy diff ( a parameter):

Capital deployed = rate_difference/max_APY_diff c [-1,1]

when Capital deployed is 1, the agent sells all possible RAI it can, if its -1 it will sell all possible RAI. The max amount is defined by a parameter.

### Parameters

1.  usd_rate_trader_max_APY_diff:Adjusts how big rate difference there need to be for agent to distribute all the funds to the market: Capital deployed = rate_difference/diff

2.  rai_borrower_max_APY_diff:Adjusts how big rate difference there need to be for agent to distribute all the funds to the market: Capital deployed = rate_difference/diff

3.  rai_lender_max_APY_diff:Adjusts how big rate difference there need to be for agent to distribute all the funds to the market: Capital deployed = rate_difference/diff

### State Variables

1.  external_USD_APY: External interest rate that agents can use to get constant 5% return over year for their USD balance

2.  compound_RAI_borrow_APY: Yearly interest rate that agents need to pay to borrow RAI

3.  compound_RAI_lend_APY: Yearly interest rate that agents get to loan RAI

1.  usd_rate_trader_state: USD rate trader state, varies between [-usd_rate_trader_max_balance,usd_rate_trader_max_balance]. It represent how much RAI the agent is SHORT at the moment

2.  usd_rate_trader_max_balance: max amount of balance the trader can go long or short

1.  Rai_borrower_state: Rai borrowers state, varies between [-rai_borrower_max_balance,rai_borrower_max_balance]. It represent how much RAI the agent is SHORT at the moment

2.  rai_borrower_max_balance: Max amount of balance the trader can go long or short

1.  rai_lender_state: Rai lenders state, varies between [-rai_lender_max_balance,rai_lender_max_balance]. It represent how much RAI the agent is SHORT at the moment

2.  rai_lender_max_balance: Max amount of balance the trader can go long or short

### Inputs

1.  Uniswap RAI and ETH delta

2.  Eth_price

3.  Market_price_twap

4.  target_price

### Outputs

1.  rai_lender_state

2.  rai_borrower_state

3.  usd_rate_trader_state

4.  ETH_delta

5.  RAI_delta

### Pseudocode behavior

#### Lender

share = -(compound_RAI_lend_APY + APY)/rai_lender_max_APY_diff

if share > 1:

share = 1

elif share < -1:

share = -1

state['compound_RAI_lend_APY'] + APY < 0:

share = 1

Adjust capital with uniswap so that we are short by share*100%

#### Borrower

share = (compound_RAI_borrow_APY - APY)/rai_borrower_max_APY_diff

if share > 1:

share = 1

elif share < -1:

share = -1

if APY < 0:

share = -1

Adjust capital with uniswap so that we are short by share*100%

#### USD Trader

share = (external_USD_APY - APY)/usd_rate_trader_max_APY_diff

if share > 1:

share = 1

elif share < -1:

share = -1

Adjust capital with uniswap so that we are short by share*100%
