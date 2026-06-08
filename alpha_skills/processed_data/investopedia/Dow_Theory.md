# Dow Theory

**Category:** Classic Trading Theories 
**Source:** Investopedia / Technical Analysis Reference

---

## 📝 Definition

**Dow Theory** is a trading framework developed by Charles Dow (co-founder of Dow Jones & Company and editor of The Wall Street Journal). It is the foundational basis for modern technical analysis, suggesting that the market is in a trend if one of its averages (e.g., Industrials) advances above a previous important high and is accompanied or followed by a similar advance in the other average (e.g., Transports).

### Six Basic Tenets of Dow Theory
1. **The Market Deploys Three Movements:**
 - **Primary Trend:** The major trend (bull or bear market) lasting from less than a year to several years.
 - **Secondary Reaction (Corrections):** Corrections to the primary trend, lasting from three weeks to three months, retracing 1/3 to 2/3 of the primary move.
 - **Minor Fluctuations:** Short-term day-to-day noise lasting from hours to less than three weeks.
2. **Market Trends Have Three Phases:**
 - **Accumulation Phase:** Informed investors buy (or sell) assets against general market opinion. Prices change little because supply matches demand.
 - **Public Participation (Trend-Following) Phase:** The price moves rapidly as the public, trend followers, and institutional investors jump in on technical signals.
 - **Distribution (Speculative) Phase:** The public goes rampant, buying heavily. Astute investors who accumulated during the first phase begin to liquidate their positions.
3. **The Market Index/Average Discounts All News:** Prices immediately reflect all past, current, and future information, including emotions and fundamentals.
4. **Market Averages Must Confirm Each Other:** A trend signal in one index (e.g., Dow Jones Industrial Average) must be confirmed by a signal in another related index (e.g., Dow Jones Transportation Average) to be valid.
5. **Volume Must Confirm the Trend:**
 - In an uptrend, volume should increase when prices rise and decrease when prices fall.
 - In a downtrend, volume should increase when prices fall and decrease when prices rise.
6. **Trends Exist Until Definitive Signals Prove Otherwise:** A trend remains in effect despite temporary noise or corrections until a reversal signal is confirmed.

---

## 🔢 Mathematical Concept & Logic

Dow Theory relies on identifying relative peaks and troughs:
- **Uptrend:** Higher Highs ($HH$) and Higher Lows ($HL$).
- **Downtrend:** Lower Highs ($LH$) and Lower Lows ($LL$).

Let $H_{local}(t, n)$ be the local peak over window $n$, and $L_{local}(t, n)$ be the local trough.
- Uptrend condition: 
 $$P_t > H_{local}(t-1, n) \quad \text{and} \quad L_{local}(t, n) > L_{local}(t-n, n)$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

Dow Theory principles translate directly into trend-following filters and volume confirmations:

1. **Volume Confirmation Indicator:**
 Multiply price momentum by volume change to confirm the trend:
 ```python
 // Positive if price goes up on high volume relative to average volume
 momentum = ts_delta(close, 5);
 vol_ratio = volume / ts_mean(volume, 20);
 signal = momentum * vol_ratio;
 rank(signal)
 ```

2. **Primary Trend Filter (Using Long Term Moving Average):**
 Only trade in the direction of the primary trend (e.g. 200 days):
 ```python
 primary_trend = close > ts_mean(close, 200);
 short_term_reversion = -ts_delta(close, 5);
 // Only take short-term mean reversion trades in the direction of the primary bull market
 signal = if_else(primary_trend, short_term_reversion, 0);
 rank(signal)
 ```

---

*Prepared as part of the Alpha Creator Skill raw data package.*