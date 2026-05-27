# Market Microstructure

**Category:** Quantitative Concepts  
**Source:** Investopedia / Quantitative Finance Reference

---

## 📝 Definition

**Market Microstructure** is the branch of financial economics that deals with details of how exchange rules, transaction costs, order type dynamics, and bid-ask spreads affect price formation and liquidity. It analyzes the specific mechanisms through which latent demands are translated into executed transactions.

### Key Microstructure Concepts
1. **Bid-Ask Spread:** The difference between the highest price a buyer is willing to pay (bid) and the lowest price a seller is willing to accept (ask).
   - *Components:* Order processing costs, inventory holding costs, and adverse selection costs (risk of trading with informed traders).
2. **Order Book Dynamics:** The collection of limit buy and sell orders waiting to be executed at different price levels. Depth refers to the volume of orders at each price.
3. **Market Impact (Slippage):** The effect that a buyer or seller has on the price of an asset when buying or selling. Large orders consume order book depth, pushing prices adversely.
4. **Adverse Selection (Kyle's Lambda / Roll's Model):** The risk that a liquidity provider trades with a counterparty who has superior or asymmetric information, leading to expected losses for the provider.
5. **Order Flow Toxicity (VPIN):** The risk that order flow is heavily dominated by informed traders, which can lead to liquidity dry-ups and flash crashes.

---

## 🔢 Mathematical Formulations

- **Proportional Bid-Ask Spread:**
  $$\text{Spread}_{prop} = \frac{P_{ask} - P_{bid}}{P_{mid}}, \quad P_{mid} = \frac{P_{ask} + P_{bid}}{2}$$

- **Roll's Spread Estimate (Using serial covariance of price changes):**
  $$\text{Roll Spread} = 2 \sqrt{-\text{Cov}(\Delta P_t, \Delta P_{t-1})}$$

---

## 💡 Application in Alpha Design (WorldQuant Brain)

In WorldQuant Brain, microstructure signals are extremely powerful for high-frequency or short-term alphas, utilizing specific transaction-level or order book datasets:

1. **Spread Reversion Alpha:**
   Stocks with wide bid-ask spreads often experience temporary price distortions due to illiquidity. These distortions tend to revert:
   ```python
   // Requires datasets containing bid-ask spread or using high-low range as a proxy
   spread_proxy = (high - low) / close;
   // Short-term reversion: sell stocks that had wide range (spread proxy) on negative returns
   signal = -rank(returns) * spread_proxy;
   rank(signal)
   ```

2. **Order Flow Imbalance (OFI Proxy):**
   OFI measures the imbalance between buy pressure and sell pressure based on volume and price direction:
   ```python
   // Positive if close is near high on high volume, negative if near low
   close_location = ((close - low) - (high - close)) / (high - low + 0.001);
   ofi_proxy = close_location * volume;
   // Smooth to create a short-term trend signal
   signal = ts_mean(ofi_proxy, 5);
   rank(signal)
   ```

---

*Prepared as part of the Alpha Creator Skill raw data package.*
