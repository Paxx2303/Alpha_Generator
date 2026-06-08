# [BRAIN TIPS] How can I use the test period to improve the OS performance of my Alpha?

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/22205077935895--BRAIN-TIPS-How-can-I-use-the-test-period-to-improve-the-OS-performance-of-my-Alpha 
**Metadata:** NL41370 2 years ago Edited

## Post Content

**Why is test period important?**

A good In Sample (IS) performance of an Alpha doesn't guarantee good Out Sample (OS) performance because the Alpha was developed using the IS data, which means it was specifically designed to fit the IS data well. The distinction between fitting and overfitting is delicate and can often lead to significant degradation of the Alpha's performance in OS.

One solution to tackle this issue is Validation. Validation involves comparing the performance of your Alpha in scenarios that differ from the data it was originally trained on. It then assesses the stability of the performance during this test period, which provides an idea about the robustness of the Alpha and its performance in the Out Sample (OS).

Using the Test Period feature on the platform, you can split the IS period into training and test period. Test Period option is available under Simulation settings while simulating an Alpha. You can then create Alphas using the training data and check its performance in the test period to see if your Alpha is overfitted or not.

**How to perform Validation on BRAIN?**

1. Split the IS period into a training and test period. As a rule of thumb, an 80-20 split between training and test data is ideal. For example, if you have a 5-year period, **setting the test period as 1 year**can help achieve this configuration.
2. Use the training data period (4-year period in this case) to develop your Alpha
3. Simulate your Alpha and compute Alpha stats for the training IS period.
4. The stats for test period are hidden by default. Compare the stats for test period with training period by clicking the “Show test period button” on top of the Simulation results.

**Best Practices**

1. If there is a decrease of more than 50% in performance stats (such as Sharpe ratio, fitness, etc.) during the test period compared to the training period, it may indicate overfitting
2. Use multiple/ longer test periods (20%, 30%, 40% of total IS period) to enhance confidence in observed training performance
3. Avoid fitting your Alphas specifically to the test period. To ensure this, evaluate the stats of the test period only after you have completed the Alpha backtesting and are satisfied with the performance in the training period
4. Use validation along with rank tests and sub/super universe tests  to assess the robustness of Alpha performance
5. Compare similar implementations of an Alpha idea using validation; submit the Alpha with the most stable performance in training and test periods.
6. You can accept or reject Alpha ideas based on drastic performance decline in the test period, which could be indicative of potential poor OS performance.

## Comments

### Comment by VS18359 1 year ago
Hi, 
Thank you so much for sharing your valuable tips on Test Period of an Alpha, which help in deciding the quality of Alpha i.e OS. Could you please explain it by taking an example, which is quite helpful.

---

### Comment by PL15523 1 year ago
You can use it based on the following example: For example, you have an alpha with sharpe 2 on the entire data. Now you cover the test for 2 years, you optimize the train to get sharpe 2, however when you turn on the test period you see sharpe is only 0.5, which proves that the alpha has been overfitted.

---

### Comment by AC63290 1 year ago
Thank you for the detailed explanation and support regarding the importance of the test period and validation in developing robust Alphas. The guidelines on splitting the IS period, evaluating performance, and identifying overfitting are incredibly helpful. The suggestion to use multiple test periods and avoid fitting Alphas specifically to the test data provides a clear path to ensure stability and robustness. Additionally, combining validation with rank tests and sub/super universe tests is an excellent way to enhance confidence in an Alpha’s performance. Your insights will undoubtedly help improve my approach to Alpha development. Thanks again for your valuable guidance!

---

### Comment by HV77283 1 year ago
Thank you for the detailed explanation on the test period and validation in Alpha development. The insights on splitting the IS period, avoiding overfitting, and using multiple test periods are very helpful. Combining validation methods adds great confidence in Alpha performance. I’ll definitely apply these strategies!

---

### Comment by TT55495 1 year ago
Thank you for the detailed explanation! The importance of the test period in validating an Alpha's performance and avoiding overfitting is now much clearer. I appreciate the practical tips on how to split the IS period, evaluate the performance, and ensure robustness using validation, rank tests, and other methods. This will definitely help in creating more reliable and effective Alphas.

---

### Comment by CC40930 1 year ago
The test period is crucial because it helps evaluate how an Alpha performs on data it hasn't seen during its creation, ensuring that it is not overfitted to the In Sample (IS) data. Overfitting occurs when an Alpha performs exceptionally well on the IS data but poorly on new, unseen data, leading to unreliable results in real-world trading. By using a test period, you can validate the stability and robustness of the Alpha's performance across different data periods, giving you greater confidence that it will perform well in the Out Sample (OS) period, which is critical for assessing long-term performance.

---

### Comment by SP61833 1 year ago
Thank you for the detailed explanation on the test period.It is an excellent way to enhance confidence in an Alpha’s performance. This will definitely help in creating more reliable and effective alphas,

---

### Comment by AK52014 1 year ago
The test period evaluates an Alpha's performance on unseen data, ensuring it isn’t overfitted to In Sample (IS) data. This validation confirms stability and robustness, building confidence in its long-term Out Sample (OS) performance.

---