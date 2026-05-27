# Sub-universe Sharpe of 0.32 is below cutoff of 0.82.

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/27479493466647-Sub-universe-Sharpe-of-0-32-is-below-cutoff-of-0-82  
**Metadata:** SH94314 1 year ago Edited

## Post Content

Please let me know what error this is, and how to fix it.

"Sub-universe Sharpe of 0.32 is below cutoff of 0.82."

## Comments

### Comment by MB13430 1 year ago
The error, "Sub-universe Sharpe of 0.32 is below cutoff of 0.82," indicates that your alpha failed the sub-universe Sharpe test, which is a robustness check performed on the BRAIN platform before submission. This test ensures that your alpha performs consistently across different subsets of the universe, particularly more liquid (or smaller) universes.

For example, if your alpha is designed for the **USA TOP3000 universe**, the platform also evaluates its performance on the smaller, more liquid**USA TOP1000 universe**. If the alpha's performance in the smaller universe is significantly worse (e.g., a lower Sharpe ratio), it suggests that the alpha relies heavily on less liquid stocks. This is a warning sign, as such alphas are less likely to perform reliably in out-of-sample testing or in real-world conditions.

To address this issue, you’ll need to improve your alpha’s robustness by ensuring it works well across different universes and isn’t overly reliant on specific subsets of stocks, like smaller or less liquid ones.

The sub-universe Sharpe test uses this formula to determine the cutoff:

**subuniverse_sharpe >= 0.75 * sqrt(subuniverse_size / alpha_universe_size) * alpha_sharpe**

---

### Comment by AG20578 1 year ago
Also this article in Learn section might help  [Sub Universe Test](https://platform.worldquantbrain.com/learn/documentation/interpret-results/alpha-submission#sub-universe-test)

---

### Comment by QG16026 1 year ago
Hi, the easiest way is you re-sim that alpha on illiquid market. Another way is multiply alpha by volume or adv20

---

### Comment by SH94314 1 year ago
[QG16026](/hc/en-us/profiles/22532757009175-QG16026)  Thanks a lot for your sharing, i will test it to see how effective it is, i encountered quite a few of these errors when building alpha

---

### Comment by PH82915 1 year ago
Diversify signals:
Incorporate additional features or data sources that are relevant to the underperforming sub-universe.
For example, if your alpha struggles in a particular region, include region-specific data (e.g., local market factors or news sentiment).
Reduce noise:
Apply feature selection techniques to remove irrelevant or overly noisy features that may hurt performance in certain sub-universes.
Blend multiple alphas:
Combine your alpha with others that complement its weaknesses in specific sub-universes.

---

### Comment by PH82915 1 year ago
### **Example Actions**

If the sub-universe is **low-cap stocks**, and your alpha struggles:

1. Add features that are specific to low-cap stocks, such as liquidity or earnings surprises.
2. Reduce reliance on volatile signals like price momentum, which might not work well for low-cap assets.

If the sub-universe is **a specific region** (e.g., Europe):

1. Include regional economic indicators or adjust your features to account for different trading hours or market structure.
2. Test whether excluding the region improves overall performance.

---

### Comment by SH94314 1 year ago
[PH82915](/hc/en-us/profiles/1532005543462-PH82915)  Your explanation is too abstract and I don't really understand this, can you give a more specific example?

---

### Comment by TN74933 1 year ago
The error message, "Sub-universe Sharpe of 0.32 is below the cutoff of 0.82," indicates that your alpha failed the sub-universe Sharpe test, a robustness check performed on the BRAIN platform before submission. This test assesses how consistently your alpha performs across different subsets of the universe, particularly in more liquid or smaller universes. To improve your alpha, consider integrating factors that account for liquidity, (volume,...) to enhance its robustness.

---

### Comment by CC40930 1 year ago
The error message indicates that your alpha's **sub-universe Sharpe ratio** (0.32) is below the required **minimum cutoff Sharpe ratio** (0.82) for a particular sub-universe. This issue arises because the alpha does not perform well on specific subsets of the overall universe, even if it might perform acceptably on the entire universe.

---

### Comment by CT68712 1 year ago
Hey everyone! I just ran into the "Sub-universe Sharpe of 0.32 is below cutoff of 0.82" error too. As a newbie in quantitative trading, I find this really insightful. It seems focusing on the robustness of my alpha across different market conditions is crucial. Thanks for the tip about improving liquidity features and diversifying signals. I'm excited to test out the suggestions like adding regional economic indicators and removing noisy signals. It's a bit overwhelming, but I'm here to learn and adapt. If anyone has more examples on how to refine this, I'd love to hear it! Keep hustling, everyone!

---

### Comment by AK52014 1 year ago
The error, "Sub-universe Sharpe of 0.32 is below cutoff of 0.82," indicates your alpha failed the robustness check on the BRAIN platform, highlighting poor performance in smaller, more liquid universes like USA TOP1000 versus USA TOP3000.

---

### Comment by KP26017 1 year ago
Please refer to this section in the learn documentation:  [Consultant Submission Tests | WorldQuant](https://platform.worldquantbrain.com/learn/documentation/consultant-information/consultant-submission-tests#sub-universe) BRAIN. One tip is to multiply alpha by volume or adv20 to put more weight on stocks with higher liquidity. (x*volume)

---

### Comment by TD17989 1 year ago
- Review the cost of goods sold (COGS) and operational costs. Can you renegotiate supplier contracts or find more cost-effective alternatives?
- Streamline processes and eliminate inefficiencies. This could mean automating certain tasks, improving inventory management, or reducing waste.

---

### Comment by FC45157 1 year ago
Thank you for sharing that insight. I would also like to gain knowledge on simulating a good alpha that will pass

---

### Comment by AC63290 1 year ago
**Fitness and Sharpness:** The combination of momentum (capturing short-term trends) with sentiment (reflecting market sentiment for Chinese assets) can be highly effective in capturing fast-moving market opportunities, increasing both fitness and sharpness.

---

### Comment by WX16829 1 year ago
Increase the Sharpe ratio, focus on enhancing the quality of your alphas:

- **Signal Strength**: Ensure that your alphas are capturing strong, persistent signals. Weak or noisy signals can lead to low Sharpe ratios.
- **Diversification**: Combine multiple alphas with low correlation to improve the overall Sharpe ratio. This can help in reducing the impact of any single underperforming alpha.

---

### Comment by VK91272 1 year ago
The error, Sub-universe Sharpe of 0.32 is below cutoff of 0.82, indicates that your alpha failed the sub-universe Sharpe test, which is a robustness check performed on the BRAIN platform before submission. This test ensures that your alpha performs consistently across different subsets of the universe, particularly more liquid (or smaller) universes.

---

### Comment by TD17989 1 year ago
Review the guidelines or rules for the theme you're working with. There may be specific constraints on how the multiplier interacts with the theme, and deviating from these constraints can trigger errors in your alpha checks.

---

### Comment by NG78013 1 year ago
The error, "Sub-universe Sharpe of 0.32 is below cutoff of 0.82," indicates your alpha failed the robustness check on the BRAIN platform, highlighting poor performance in smaller, more liquid universes like USA TOP3000.

---

### Comment by NN89351 1 year ago
The error message **"Sub-universe Sharpe of 0.32 is below the cutoff of 0.82"** means your alpha didn’t pass the sub-universe Sharpe test—a key robustness check on the BRAIN platform. This test evaluates how well your alpha holds up across different subsets, especially in more liquid or smaller universes. To improve it, you might want to incorporate factors that address liquidity to make the signal more stable.

---

### Comment by HV77283 1 year ago
For low-cap stocks, add features like liquidity or earnings surprises and reduce reliance on volatile signals. For specific regions, include regional indicators, adjust for market structure, or test exclusion.

---