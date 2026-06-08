# [BRAIN TIPS] Sequencing Multiple Operators in an Expression

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/19344464221335--BRAIN-TIPS-Sequencing-Multiple-Operators-in-an-Expression 
**Metadata:** NL41370 2 years ago Edited

## Post Content

Sequencing many operators in a logical sense can potentially reduce correlation or enhance the performance of an Alpha. The rationale behind this is that applying transformational operators changes the weights assigned to each stock, which can, in turn, alter the profit and loss (PnL). As a result, the correlation may decrease, potentially improving the performance of the Alpha.

For examples, consider the below Alpha:

Now applying “quantile()” outside of the Alpha and you can see the Sharpe ratio increases significantly.

Here are some best practices for this approach:

- Preserve the simplicity of outer operators to keep the original idea. For instance, “rank(ts_rank(data field))” is preferable to “ts_rank(rank(data field))”. For more ideas on using operators, refer to: [Improve your Alphas with Signal Smoothing](/hc/en-us/community/posts/14588500172567--BRAIN-TIPS-Improve-your-alphas-with-Signal-Smoothing) .
- Avoid using too many operators just to boost performance, as this can lead to overfitting.

When combining two sub-expressions, use scaling operators as the outermost operator on the sub-expressions. However, before combining expressions of Alphas, please read [Why is linear combination of expressions in one Alpha not recommended?](/hc/en-us/community/posts/15238236356375--BRAIN-TIPS-Why-is-linear-combination-of-expressions-in-one-alpha-not-recommended-)

## Comments

### Comment by TN48752 1 year ago
I would like to ask why the turnover increases when nesting cross sectional functions outside alpha? Does removing outliers cause the portfolio conversion rate to increase? Hope you can explain. Thank you very much.

---

### Comment by PL15523 1 year ago
Hi, I can't find the mdf_ dataset. It seems to be out of service. Is there any dataset similar to this one? Thank you very much.

---

### Comment by DP11917 1 year ago
I would like to ask that in everyone's opinion, how many operators should be nested to ensure low correlation and avoid overfitting?

---

### Comment by AC63290 1 year ago
The article effectively emphasizes using logical operator sequencing to enhance Alpha performance while maintaining simplicity. Practical examples like applying "quantile()" demonstrate improvements. However, additional clarity on when operator combinations risk overfitting and specific examples of scaling operator usage would further solidify understanding and practical application of these best practices.

---

### Comment by TT55495 1 year ago
How can sequencing multiple operators logically improve the performance of an Alpha model, and what are some best practices to avoid overfitting when applying transformations to data?

---

### Comment by LK29993 1 year ago
Hi TN48752!

Previously when we only have the ts_rank() operator, the turnover may be lower because the fluctuations in Alpha value for each stock come from trend fluctuations in the stock's own input data value. After applying the cross-sectional operator, we are now also comparing the trend fluctuations of the stocks in the selected universe, i.e. there is now another layer of variation. This results in more variation in the alpha values for each day, and thus higher turnover.

Could you share more about what "portfolio conversion rate" refers to?

---

### Comment by LK29993 1 year ago
Hi PL15523! Yes, the mdf dataset is no longer available. You can find more fundamental model datasets here: Data Explorer tab > Browse by category > Fundamental > Fundamental Models.

---

### Comment by LK29993 1 year ago
Hi DP11917! It really depends on your Alpha idea and the role each operator plays in your Alpha. Generally, the less operators you use, the less likelihood of overfitting.

---

### Comment by HV77283 1 year ago
Sequencing operators logically can reduce correlation and enhance Alpha performance by altering stock weights and PnL. Keep outer operators simple to maintain clarity, avoid excessive operators to prevent overfitting, and use scaling operators when combining sub-expressions for robust results.

---

### Comment by CC40930 1 year ago
Sequencing operators logically can help reduce correlation and improve Alpha performance by adjusting stock weights. For example, applying “quantile()” outside the Alpha can significantly boost the Sharpe ratio. Best practices include maintaining simplicity in outer operators to preserve the core idea, avoiding excessive use of operators to prevent overfitting, and scaling sub-expressions appropriately.

---