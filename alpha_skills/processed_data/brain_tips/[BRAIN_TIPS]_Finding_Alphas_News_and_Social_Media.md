# [BRAIN TIPS] Finding Alphas: News and Social Media

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/20051406364695--BRAIN-TIPS-Finding-Alphas-News-and-Social-Media 
**Metadata:** NL41370 2 years ago Edited

## Post Content

The book “ [**Finding Alphas**](https://www.amazon.com/Finding-Alphas-Quantitative-Approach-Strategies-dp-1119571219/dp/1119571219/ref=dp_ob_image_bk) " by Igor Tulchinsky et al explores Alpha ideas related to news data. In Chapter 22, the article "The Impact of News and Social Media on Stock Returns" discusses five Alpha ideas: sentiment, novelty or uniqueness, relevance, no news is good news, and news momentum. [**[1]**](https://onlinelibrary.wiley.com/doi/10.1002/9781119571278.ch22)

To apply these Alpha ideas on the BRAIN platform, the recommended dataset is the Ravenpack News Dataset. It has fields such as " [***nws18_bee***](https://platform.worldquantbrain.com/data/data-sets/news18/data-fields/nws18_bee?delay=1&instrumentType=EQUITY&region=USA&universe=TOP3000) " for sentiment, " [***rp_nip_assets***](https://platform.worldquantbrain.com/data/data-sets/news18/data-fields/rp_nip_assets?delay=1&instrumentType=EQUITY&region=USA&universe=TOP3000) " for novelty or uniqueness, and " [***nws18_relevance***](https://platform.worldquantbrain.com/data/data-sets/news18/data-fields/nws18_relevance?delay=1&instrumentType=EQUITY&region=USA&universe=TOP3000) " and " [***nws18_qcm***](https://platform.worldquantbrain.com/data/data-sets/news18/data-fields/nws18_qcm?delay=1&instrumentType=EQUITY&region=USA&universe=TOP3000) " for relevance.

Here is a concise summary of the book and suggestions on how to apply them on the BRAIN platform:

1. **Sentiment:** Use the sentiment score provided in the Ravenpack News Dataset (i.e. nws18_bee) to inform decisions based on positive, negative, or neutral sentiment.
2. **Novelty or Uniqueness:** Use the news impact projection of assets (i.e. rp_nip_assets) to identify news containing new and unique information that has the potential to influence stock prices significantly.
3. **Relevance:** Consider the relevance of news to specific companies using data fields such as nws18_relevance and nws18_qcm to enhance Alpha signals and capture emotional signals related to highly relevant news.
4. **No News is Good News:** Explore Alpha ideas that stocks sensitive to news may experience reduced institutional investment flows when uncertainty increases.
5. **News Momentum:** Analyze news data to identify potential trends in the stock market when news is not efficiently reflected in stock prices.

For more detailed information and specific examples, please refer to the book "Finding Alphas" chapter 22 and explore the relevant datasets and fields available in the BRAIN platform!

[**[1] Chapter 22. The Impact of News and Social Media on Stock Returns**](https://onlinelibrary.wiley.com/doi/10.1002/9781119571278.ch22)

## Comments

### Comment by SK90981 1 year ago
Thank you for this wonderful series. It helps me to explore news and social media dataset and make alphas on these data fields. These data fields add uniqueness to my alpha. News and social media dataset help me to reduce self-correlation of my alpha.

---

### Comment by TT55495 1 year ago
Hopefully there will be more webinars on creating alpha on these datasets. I feel like news and social are the two hardest categories to create alpha from in the Data Brain category.

---

### Comment by PL15523 1 year ago
I noticed that news datasets often have very high turnover, probably due to hourly or minutely update frequency. Are there any methods to capture the signal effectively?

---

### Comment by HV77283 1 year ago
Thank you for this fantastic series! It has been incredibly helpful in exploring news and social media datasets for creating unique alphas. These datasets play a crucial role in reducing self-correlation, adding a valuable dimension to my alpha strategies. Looking forward to applying these insights!

---

### Comment by AC63290 1 year ago
"Finding Alphas" explores leveraging news data for Alpha generation. Chapter 22 highlights sentiment, novelty, relevance, "no news is good news," and news momentum. On the BRAIN platform, use the Ravenpack dataset fields like "nws18_bee" for sentiment and "rp_nip_assets" for novelty to develop actionable strategies based on news-driven insights.

---

### Comment by LK29993 1 year ago
Hi PL15523!

News datasets could have high turnover due to different reasons.

If it's due to low coverage issues, where missing data cause alpha weights to keep fluctuating to zero positions resulting in high turnover, then backfilling the data using the ts_backfill operator could work.

If it's due to too frequent changes in data, operators that limit the changes could work, such as hump and hump_decay operators.

---

### Comment by CC40930 1 year ago
The book "Finding Alphas" discusses Alpha ideas related to news data, with Chapter 22 covering five key concepts: sentiment, novelty or uniqueness, relevance, no news is good news, and news momentum. To apply these on the BRAIN platform, you can utilize the Ravenpack News Dataset, which provides valuable fields for analysis.

---

### Comment by DP11917 1 year ago
The **book *“Finding Alphas”* by Igor Tulchinsky et al.** provides a detailed exploration of how to create **Alpha strategies** using various types of data, including **news data**. Specifically, Chapter 22 of the book, titled "**The Impact of News and Social Media on Stock Returns**," introduces five Alpha ideas that leverage **news sentiment, uniqueness, relevance, absence of news, and news momentum** to inform trading decisions.

---