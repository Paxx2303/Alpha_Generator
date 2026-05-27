# Sample Alpha Concepts

**Source:** https://platform.worldquantbrain.com/learn/documentation/examples/sample-alpha-concepts

[Documentation](/learn/documentation)  [](/learn/documentation)

## ⭐ Alpha Examples for Bronze Users 🥉

## Table of Contents

- [Valuation based on cash flow](#valuation-based-on-cash-flow)
- [Overpriced stocks](#overpriced-stocks)
- [Volatility arbitrage](#volatility-arbitrage)

Valuation based on cash flow

**Hypothesis**

A lower EV/CF usually suggests the company is becoming cheaper relative to its cash-generating ability; a higher multiple suggests it’s getting more expensive.

**Implementation**

Use ts_zscore to standardize the chang of the ratio and group_rank to control the turnover.

**Hint to Improve Alpha**

There are various types of cash flow, and switching the type used in the metric may improve its performance.

1

group_rank(-ts_zscore(enterprise_value/cashflow, 63),industry)

Open example alpha in Simulate

Simulation Settings

RegionUniverseLanguageDecayDelayTruncationNeutralizationPasteurizationLookbackMax TradeMax PositionUSATOP3000Fast Expression010.08IndustryOnOFFOFF

Region: USA

Universe: TOP3000

Language: Fast Expression

Decay: 0

Delay: 1

Truncation: 0.08

Neutralization: Industry

Pasteurization: On

Lookback:

Max Trade: OFF

Max Position: OFF

Overpriced stocks

**Hypothesis**

When analyst price target estimates (est_ptp) and free cashflow estimates (est_fcf) move highly in sync over the past month (high positive correlation), it may signal that the market has already fully priced in the cash flow expectations into price targets — leaving little room for further upside.

**Implementation**

Using est_ptp to capture price estimate and est_fcf to capture free cash flow and calculate the dynamics between them with ts_corr.

**Hint to Improve Alpha**

The window of 1 year might be too long to react on the price correction. Try shorter window.

1

-ts_corr(est_ptp,est_fcf,252)

Open example alpha in Simulate

Simulation Settings

RegionUniverseLanguageDecayDelayTruncationNeutralizationPasteurizationLookbackMax TradeMax PositionUSATOP3000Fast Expression010.08MarketOnOFFOFF

Region: USA

Universe: TOP3000

Language: Fast Expression

Decay: 0

Delay: 1

Truncation: 0.08

Neutralization: Market

Pasteurization: On

Lookback:

Max Trade: OFF

Max Position: OFF

Volatility arbitrage

**Hypothesis**

Higher volatility is often observed during bearish markets, while lower volatility is typically seen during bullish markets. A lower Parkinson's volatility coupled with a higher implied volatility may suggest that there could be a stronger bullish sentiment for the stock in the future.

**Implementation**

Long the stock if its implied volatility significantly exceeds its historical volatility and short the opposite

**Hint to Improve Alpha**

Can you use ts_backfill to avoid missing data on certain days?

1

implied_volatility_call_120/parkinson_volatility_120

Open example alpha in Simulate

Simulation Settings

RegionUniverseLanguageDecayDelayTruncationNeutralizationPasteurizationLookbackMax TradeMax PositionUSATOP200Fast Expression010.08SectorOnOFFOFF

Region: USA

Universe: TOP200

Language: Fast Expression

Decay: 0

Delay: 1

Truncation: 0.08

Neutralization: Sector

Pasteurization: On

Lookback:

Max Trade: OFF

Max Position: OFF

[Prev: ⭐ Alpha Examples for Beginners](/learn/documentation/examples/19-alpha-examples)