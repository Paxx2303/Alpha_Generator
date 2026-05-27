# Comparing Stocks to Peers

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/23581999495831-Comparing-Stocks-to-Peers  
**Metadata:** SA89201 2 years ago

## Post Content

One of the example alphas gave the hint of comparing a stock to its "peers" instead of to the market as a whole. Beyond neutralization choice, what are some other ways to do so?

## Comments

### Comment by AG20578 2 years ago
Hi!

Beyond neutralization choice, there are more ways to compare a stock to its "peers". Consider using  [group operators](https://platform.worldquantbrain.com/learn/data-and-operators/operators#group-operators) , like group_zscroe or group_rank.

Additionally, you're not limited to the standard groups of industry, sector, or market found in the settings. Explore the DataExplorer to discover available  [grouping fields.](https://platform.worldquantbrain.com/data/data-fields?delay=1&instrumentType=EQUITY&limit=20&offset=0&region=USA&type=GROUP&universe=TOP3000)  You can also use the  [bucket operator](https://platform.worldquantbrain.com/learn/data-and-operators/detailed-operator-descriptions#bucket)  to create custom groups!

---

### Comment by QG16026 1 year ago
I would like to ask that when comparing with cross-sectional functions, does it mean that alpha is long only? Because as I understand, the weights will be scaled from 0 to 1, which means that all are positive weights. But I don't quite understand because in theory the total weight must be 0. I hope to get an answer.

---

### Comment by LN78195 1 year ago
Regarding cross-sectional functions, how do you ensure total weight neutrality when weights are scaled positively? Would love to hear more about how this is implemented effectively.

---

### Comment by deleted user 1 year ago
Hi, I would like to ask if the functions when deployed normally and its group by market are similar? For example: rank and group rank (x, market) or scale and group scale (x,market)

---

### Comment by DP11917 1 year ago
I would like to ask if there are any other functions besides cross sectional functions that help remove outliers?

---

### Comment by LK29993 1 year ago
Hi QG16026 and LN78195!

1) Not all cross-sectional functions will result in values in the range of 0 to 1. For example, the output of the zscore operator could include negative values too.

2) I believe you're referring to the rank operator for outputs in the range of 0 to 1. Even though at the alpha expression level, the output will be in the range of 0 to 1, there will be a neutralization step that takes place after that based on your **Neutralization setting**. This neutralization step will subtract the mean from each of the Alpha values, so that the sum of the total Alpha values is zero.

---

### Comment by LK29993 1 year ago
Hi TK95999! Group operators are a type of cross-sectional operator but at a finer level, where the cross-sectional operation is applied within each group (as defined by the group operator), rather than across the entire universe (as defined in the simulation settings).

---

### Comment by LK29993 1 year ago
Hi DP11917! Time series operators can work too.

---

### Comment by CC40930 1 year ago
Beyond neutralization, you can compare a stock to its peers using group-based operators like `group_mean()`, `group_max()`, or `group_min()`, which allow you to compare a stock's performance to others within the same group (e.g., sector, industry, or region). Another approach could be using z-scores or percentiles to standardize values within a group, making it easier to identify outliers compared to similar stocks.

---

### Comment by DP11917 1 year ago
When comparing a stock to its **peers** rather than the market as a whole, you're shifting the focus from **market-wide risk** to **sector-specific or industry-specific dynamics**. This approach is beneficial because it takes into account the fact that stocks in the same sector or industry often share similar economic drivers, risks, and opportunities, and their performance may be more closely correlated with each other than with the overall market.

---

### Comment by CT68712 1 year ago
Hi there! As someone learning about quantitative trading, I find the concept of comparing stocks to peers fascinating. Utilizing group-based operators like group_mean or group_rank makes such comparisons more precise. It's interesting how focusing on sector or industry dynamics rather than the entire market allows for a deeper analysis of performance. I often wonder how these techniques help in identifying potential investment opportunities. Exploring the available grouping fields in the DataExplorer is a great idea to enhance our strategies! Can't wait to dive deeper into this!

---

### Comment by AK52014 1 year ago
Beyond neutralization, use group-based operators like group_mean(), group_max(), or group_min() to compare a stock’s performance within its group. Alternatively, apply z-scores or percentiles to standardize values, identifying outliers relative to similar stocks effectively.

---