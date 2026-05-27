# Incorporating Volatility into Chinese Market Trades

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/23726331730327-Incorporating-Volatility-into-Chinese-Market-Trades  
**Metadata:** SA89201 2 years ago

## Post Content

One of the bronze alpha ideas involved going long on the stocks with low volume in the Chinese market and short on those with high volume. One of the suggestions for improving the alpha suggested incorporating volatility, but I'm not sure which datasets tell us about volatility in the Chinese market (all the obvious volatility ones seem to only exist for the US market). Any help here would be appreciated!

## Comments

### Comment by AG20578 2 years ago
Hi!

There is an interesting post on the forum about the trade_when operator, please check it out:  [Using trade_when for Event Alphas and Low Turnover Alphas](/hc/en-us/community/posts/8360363631127) 
Additionally, volatility is often measured as: ts_stddev(returns, d).
You can try using ts_rank(ts_stddev(returns, d1), d2)>0.5 as a condition in trade_when to capture periods of high volatility.

Hope it helps!

---

### Comment by QG16026 1 year ago
Hi, I don't quite understand why the CHN market needs robust universe return and sharpe backtests? Is there any way to improve these 2 indicators?

---

### Comment by AC63290 1 year ago
To incorporate volatility into your Alpha for the Chinese market, consider constructing a proxy for volatility using available datasets. For example:

1. **Price Range:** Use the daily high-low price range or the difference between the daily open and close as a measure of volatility.
2. **Rolling Standard Deviation:** Compute the rolling standard deviation of daily returns over a fixed period (e.g., 5 or 10 days) to capture recent volatility trends.
3. **Volume Implied Volatility:** Analyze the relationship between changes in trading volume and price movements as an indirect indicator of volatility.

These methods can help you approximate volatility even when explicit datasets are unavailable.

---

### Comment by ND68030 1 year ago
The Chinese stock market has options trading, such as the **China Financial Futures Exchange (CFFEX)**, where you can find implied volatility for Chinese stocks and indices. If available, implied volatility from these options can serve as a good proxy for market expectations of volatility.

---

### Comment by LN78195 1 year ago
To incorporate volatility into Chinese market trades, consider constructing proxies such as rolling standard deviation of returns, daily high-low price range, or volume-implied volatility. Additionally, explore implied volatility from options on platforms like CFFEX for a more direct measure tailored to the Chinese market. Which approach do you think aligns best with your alpha's objectives?

---

### Comment by HV77283 1 year ago
Interesting alpha idea of going long on low-volume stocks and short on high-volume ones in the Chinese market! For volatility data, you might explore local sources or financial platforms specific to China, as many US-focused datasets may not cover it. Any suggestions on regional volatility data would be helpful!

---

### Comment by AM60509 1 year ago Edited
In order to introduce volatility into the alpha ,multiply the alpha by rank(ts_stddev(returns,25) or rank (ts_stddev(alpha1,lookback period) where alpha1 is the alpha expression

---

### Comment by TT55495 1 year ago
Can you explain why it's essential to focus on robust universe returns and Sharpe ratio backtests in the CHN market? Also, what are some methods to improve the reliability and performance of these indicators in this context?

---

### Comment by NH84459 1 year ago
Incorporating **volatility** into your alpha strategy for the **Chinese market** can be a great improvement, but you're right that most readily available datasets tend to focus on **US markets**. However, there are **several datasets and approaches** specific to the **Chinese market** that you can explore.

---

### Comment by CC40930 1 year ago
To incorporate volatility in your alpha for the Chinese market, you can calculate it from historical price data using standard deviation or use proxies like price dispersion or moving averages. You might also find volatility data for Chinese indices like the Shanghai Composite or CSI 300 to help.

---

### Comment by AK52014 1 year ago
To incorporate volatility into your Chinese market Alpha, use proxies like daily price ranges, rolling standard deviations of returns over periods (e.g., 5–10 days), or volume-price relationships as indirect volatility indicators when explicit datasets are unavailable.

---