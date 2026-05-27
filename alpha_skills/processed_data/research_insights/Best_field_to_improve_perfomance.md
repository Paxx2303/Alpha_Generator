# Best field to improve perfomance.

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/38021234963351-Best-field-to-improve-perfomance  
**Metadata:** DC84186 3 months ago

## Post Content

Are there categories of fields that are generally more robust for beginners.

## Comments

### Comment by MH52691 3 months ago
Fundamental data.

---

### Comment by QW33041 3 months ago
You can try Analyst Estimate Data for Equity dataset.

---

### Comment by Emmanuel Bani Menza(EM97072) 2 months ago
As a beginner, I’ve found that momentum and volatility-based fields are a good starting point. For example, using price changes (ts_delta) combined with risk control like standard deviation (ts_std_dev) helps create more stable alphas.

I’m also starting to explore fundamental data such as revenue growth, which seems promising for building stronger signals over time.

Would you recommend focusing more on price-based signals first before moving fully into fundamentals, or combining both early on?

---

### Comment by EN49135 1 month ago Edited
1. ts_rank(operating_profit_before_interest_tax/close ,220)*rank(-returns)

- This alpha identifies stocks with strong and improving operating profitability relative to their price over a 220-day period, while also favoring those that have recently underperformed. It combines a fundamental valuation signal with a short-term mean reversion effect, aiming to capture undervalued stocks that may rebound.

---