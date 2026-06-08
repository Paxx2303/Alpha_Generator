# HOW DECAY INFLUENCES TURNOVER

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/37582504908567-HOW-DECAY-INFLUENCES-TURNOVER 
**Metadata:** VO10010 4 months ago

## Post Content

Decay acts as a smoothing mechanism designed to lower an alpha’s Turnover. By averaging current signal values with previous days, it prevents the model from reacting too violently to daily price fluctuations.
Summary of the Relationship:
 1.Turnover Reduction: As you increase the Decay value, the daily change in your portfolio positions decreases. This helps your alpha stay within the required turnover limits (typically under 70%).
 2. While higher Decay improves your Fitness score by lowering transaction costs, it can negatively impact your Sharpe Ratio if the signal is time-sensitive, as the alpha becomes slower to respond to new data.
 3. Optimization: The goal is to find the minimum Decay necessary to meet turnover requirements without losing the predictive edge of the underlying logic.