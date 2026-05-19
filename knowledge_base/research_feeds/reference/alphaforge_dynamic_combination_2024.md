# AlphaForge: Dynamic Factor Combination (arXiv 2406.18394, 2024)

## Core Innovation
Instead of fixed factor weights, **re-rank and re-fit** the linear combination of factors every day using the most recent performance metrics (IC, ICIR, RankIC).

## Key Mechanism
1. Daily re-ranking of factors in the "factor zoo"
2. Select top-N factors based on recent performance
3. Fit linear model on last N days to predict current combination
4. Mega-Alpha = dynamic weighted sum

## Lesson for Hermes/DeerFlow Generation

### Static vs Dynamic Thinking
- Old way: Generate one fixed expression
- Better way: Generate expressions that are **robust to factor rotation**

### Practical Prompt Addition
When generating, add context:
```
"Generate alphas that remain effective even when recent factor performance changes.
Prefer multi-horizon and volume-price interaction signals."
```

## Recommended Generation Strategy
- Produce a diverse set of alphas across different motifs (momentum, reversion, volume, volatility)
- Avoid over-concentration in one motif family
- This naturally supports dynamic combination later

**Source:** Shi et al., AlphaForge, arXiv 2024
