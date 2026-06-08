# 19 Alpha Examples

**Source:** https://platform.worldquantbrain.com/learn/documentation/examples/19-alpha-examples

[Documentation](/learn/documentation) [Next: ⭐ Alpha Examples for Bronze Users 🥉](/learn/documentation/examples/sample-alpha-concepts)

## ⭐ Alpha Examples for Beginners

## Table of Contents

- [Operating Earnings Yield](#operating-earnings-yield)
- [Appreciation of liabilities](#appreciation-of-liabilities)
- [Power of leverage](#power-of-leverage)
- [Earnings Yield Momentum](#earnings-yield-momentum)
- [Short-Term Sentiment Volume Stability](#short-term-sentiment-volume-stability)

Operating Earnings Yield

**Hypothesis**

If the operating income of a company is currently higher than its past 1 year history, buy the company’s stock and vice-versa.

**Implementation**

Using ts_rank to identify current performance of the company compared to its own history, using the fundamental data field "operating_income".

**Hints to Implement**

Rather than comparing the value directly, can calculating a ratio that includes stock market moves, improve the signal?

1

ts_rank(operating_income,252)

Open example alpha in Simulate

Simulation Settings

RegionUniverseLanguageDecayDelayTruncationNeutralizationPasteurizationLookbackMax TradeMax PositionUSATOP3000Fast Expression010.08SubindustryOnOFFOFF

Region: USA

Universe: TOP3000

Language: Fast Expression

Decay: 0

Delay: 1

Truncation: 0.08

Neutralization: Subindustry

Pasteurization: On

Lookback:

Max Trade: OFF

Max Position: OFF

Appreciation of liabilities

**Hypothesis**

An increase in the fair value of liabilities could indicate a higher cost than expected. This may deteriorate the company's financial health, potentially leading to lower profitability or financial distress.

**Implementation**

Go short when there is an increase in the fair value of liabilities within a year and long when the opposite occurs using fundamental data.

**Hints to Implement**

Could observing the increase over a shorter period improve accuracy?

1

-ts_rank(fn_liab_fair_val_l1_a,252)

Open example alpha in Simulate

Simulation Settings

RegionUniverseLanguageDecayDelayTruncationNeutralizationPasteurizationLookbackMax TradeMax PositionUSATOP3000Fast Expression010.08SubindustryOnOFFOFF

Region: USA

Universe: TOP3000

Language: Fast Expression

Decay: 0

Delay: 1

Truncation: 0.08

Neutralization: Subindustry

Pasteurization: On

Lookback:

Max Trade: OFF

Max Position: OFF

Power of leverage

**Hypothesis**

Companies with high liability-to-asset ratios – excluding those with poor financial health or weak cashflows – often leverage debt as a strategic tool to pursue aggressive growth initiatives. By effectively utilizing financial leverage, these firms are more likely to deliver outsized returns, as they reinvest borrowed capital into high-potential opportunities.

**Implementation**

Use the ‘liabilities’ and ‘assets’ to design the ratio.

**Hint to improve the Alpha**

This ratio can vary significantly across industries. Would it be worth considering alternative neutralization settings?

1

liabilities/assets

Open example alpha in Simulate

Simulation Settings

RegionUniverseLanguageDecayDelayTruncationNeutralizationPasteurizationLookbackMax TradeMax PositionUSATOP3000Fast Expression010.01MarketOnOFFOFF

Region: USA

Universe: TOP3000

Language: Fast Expression

Decay: 0

Delay: 1

Truncation: 0.01

Neutralization: Market

Pasteurization: On

Lookback:

Max Trade: OFF

Max Position: OFF

Earnings Yield Momentum

**Hypothesis**

Stocks whose earnings yield has been high more often over the last quarter, relative to their own history, may be undervalued thus we should long them

**Implementation**

Use EPS-to-price ratio as earnings yield proxy, compare over its own past, and compare it within its industry.

**Hint to improve the Alpha**

Use NAN HANDLING to preprocess data and boost the performance

1

group_rank(ts_rank(est_eps/close, 60),industry)

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

Short-Term Sentiment Volume Stability

**Hypothesis**

A high 10-day standard deviation of sentiment volume for a stock means that investor attention is unstable, with frequent spikes and drops in how much the stock is discussed. This unstable attention is often driven by short-lived news or hype and may lead to noisy, unsustainable price moves, causing the stock to underperform afterward.

**Implementation**

Take the 10-day rolling standard deviation of relative sentiment volume scl12_buzz and negate it.

**Hint to improve the Alpha**

Would observing stability over a shorter horizon be more effective for more liquid stocks?

1

-ts_std_dev(scl12_buzz, 10)

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

[Next: ⭐ Alpha Examples for Bronze Users 🥉](/learn/documentation/examples/sample-alpha-concepts)