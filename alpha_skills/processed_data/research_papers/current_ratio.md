# current ratio

**Source:** https://support.worldquantbrain.com/hc/en-us/community/posts/39233088451863-current-ratio 
**Metadata:** BK68311 2 months ago

## Post Content

// Fundamental fields assumed:
// liabilities, fn_assets_fair_val_l1_q (assets), equity, ebit, interest_expense

// Ratios
let liab_to_assets = liabilities / fn_assets_fair_val_l1_q;
let debt_to_equity = liabilities / equity;
let interest_coverage = ebit / interest_expense;

// Optional trend
let liab_trend = (liabilities / liabilities_lag) - 1.0;

// Normalize each ratio (rank or z-score)
let score_liab_assets = rank(liab_to_assets);
let score_debt_equity = rank(debt_to_equity);
let score_interest_cov = rank(interest_coverage);
let score_liab_trend = rank(liab_trend);

// Composite alpha with weights
let w1 = 0.35; // liabilities-to-assets
let w2 = 0.25; // debt-to-equity
let w3 = 0.25; // interest coverage
let w4 = 0.15; // liabilities trend

let composite_alpha = (w1 * score_liab_assets) +
                      (w2 * score_debt_equity) +
                      (w3 * score_interest_cov) +
                      (w4 * score_liab_trend);

// Final ranking
rank(composite_alpha)

## Comments

### Comment by KS26491 1 month ago
Thanks for the info it's helpful!!!

---