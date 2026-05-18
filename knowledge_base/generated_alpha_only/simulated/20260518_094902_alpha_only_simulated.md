# Alpha Only Simulated Evaluation - 20260518_094902

- Pack: C:\Using\Alpha_Generator\knowledge_base\generated_alpha_only\20260518_072155_hermes_deerflow_alpha_only.md
- Total unique expressions: 19
- Cache reused: 11
- Live simulations run: 8
- Approved: 1

## Top Candidates

```json
[
  {
    "expression": "rank(close / ts_mean(close,20) - 1)",
    "cache_used": true,
    "status": "tested",
    "metrics": {
      "sharpe": 2.431,
      "fitness": 2.201,
      "annual_returns": 0.093,
      "turnover": 0.766,
      "drawdown": 0.283,
      "self_correlation": 1.0,
      "notes": "Turnover above maximum.; Self-correlation above maximum."
    },
    "gate_reasons": [
      "Turnover above maximum.",
      "Self-correlation above maximum."
    ]
  },
  {
    "expression": "rank(ts_corr(volume,returns,5))",
    "cache_used": true,
    "status": "approved",
    "metrics": {
      "sharpe": 2.215,
      "fitness": 1.728,
      "annual_returns": 0.18,
      "turnover": 0.078,
      "drawdown": 0.224,
      "self_correlation": 0.63,
      "notes": ""
    },
    "gate_reasons": []
  },
  {
    "expression": "rank(close / ts_mean(close,5) - 1)",
    "cache_used": true,
    "status": "tested",
    "metrics": {
      "sharpe": 2.077,
      "fitness": 0.888,
      "annual_returns": 0.111,
      "turnover": 0.14,
      "drawdown": 0.072,
      "self_correlation": 1.0,
      "notes": "Fitness below threshold.; Self-correlation above maximum."
    },
    "gate_reasons": [
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ]
  },
  {
    "expression": "rank(-ts_delta(vwap, 5))",
    "cache_used": false,
    "status": "tested",
    "metrics": {
      "sharpe": 1.36,
      "fitness": 0.77,
      "annual_returns": 0.1094,
      "turnover": 0.3448,
      "drawdown": 0.0705,
      "self_correlation": 1.0,
      "notes": ""
    },
    "gate_reasons": [
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_FITNESS.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ]
  },
  {
    "expression": "rank(-ts_delta(close,10))",
    "cache_used": false,
    "status": "tested",
    "metrics": {
      "sharpe": 1.1,
      "fitness": 0.68,
      "annual_returns": 0.0881,
      "turnover": 0.2291,
      "drawdown": 0.0681,
      "self_correlation": 1.0,
      "notes": ""
    },
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ]
  }
]
```

## Bottom Candidates

```json
[
  {
    "expression": "rank(ts_mean(returns,5))",
    "cache_used": true,
    "status": "tested",
    "metrics": {
      "sharpe": -1.12,
      "fitness": -0.67,
      "annual_returns": -0.1262,
      "turnover": 0.3489,
      "drawdown": 0.7134,
      "self_correlation": 1.0,
      "notes": "WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum."
    },
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ]
  },
  {
    "expression": "rank(ts_delta(close, 5) / ts_std_dev(close, 5))",
    "cache_used": true,
    "status": "tested",
    "metrics": {
      "sharpe": -1.12,
      "fitness": -0.57,
      "annual_returns": -0.0979,
      "turnover": 0.3771,
      "drawdown": 0.53,
      "self_correlation": 1.0,
      "notes": "deerflow pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL"
    },
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ]
  },
  {
    "expression": "rank(ts_delta(close,60) / ts_std_dev(close,60))",
    "cache_used": true,
    "status": "tested",
    "metrics": {
      "sharpe": -0.66,
      "fitness": -0.51,
      "annual_returns": -0.0743,
      "turnover": 0.1149,
      "drawdown": 0.4304,
      "self_correlation": 1.0,
      "notes": "WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL"
    },
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ]
  },
  {
    "expression": "rank(ts_delta(close,10) / ts_std_dev(close,10))",
    "cache_used": true,
    "status": "tested",
    "metrics": {
      "sharpe": -0.66,
      "fitness": -0.32,
      "annual_returns": -0.0584,
      "turnover": 0.2504,
      "drawdown": 0.3278,
      "self_correlation": 1.0,
      "notes": "deerflow pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL"
    },
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ]
  },
  {
    "expression": "rank(close / ts_mean(close, 60) - 1)",
    "cache_used": false,
    "status": "tested",
    "metrics": {
      "sharpe": -0.62,
      "fitness": -0.51,
      "annual_returns": -0.0841,
      "turnover": 0.1006,
      "drawdown": 0.4722,
      "self_correlation": 1.0,
      "notes": ""
    },
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ]
  }
]
```

## Full Results

```json
[
  {
    "expression": "rank(ts_mean(returns,5))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -1.12,
      "fitness": -0.67,
      "annual_returns": -0.1262,
      "turnover": 0.3489,
      "drawdown": 0.7134,
      "self_correlation": 1.0,
      "notes": "WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum."
    }
  },
  {
    "expression": "rank(ts_mean(returns,10))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -0.59,
      "fitness": -0.31,
      "annual_returns": -0.0641,
      "turnover": 0.2268,
      "drawdown": 0.3843,
      "self_correlation": 1.0,
      "notes": "WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum."
    }
  },
  {
    "expression": "rank(ts_mean(returns,20))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -0.59,
      "fitness": -0.39,
      "annual_returns": -0.0651,
      "turnover": 0.1528,
      "drawdown": 0.4091,
      "self_correlation": 1.0,
      "notes": "WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum."
    }
  },
  {
    "expression": "rank(ts_mean(returns,60))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 0.981,
      "fitness": 0.606,
      "annual_returns": 0.143,
      "turnover": 0.149,
      "drawdown": 0.231,
      "self_correlation": 1.0,
      "notes": "Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum."
    }
  },
  {
    "expression": "rank(close / ts_mean(close,5) - 1)",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 2.077,
      "fitness": 0.888,
      "annual_returns": 0.111,
      "turnover": 0.14,
      "drawdown": 0.072,
      "self_correlation": 1.0,
      "notes": "Fitness below threshold.; Self-correlation above maximum."
    }
  },
  {
    "expression": "rank(close / ts_mean(close,20) - 1)",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Turnover above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 2.431,
      "fitness": 2.201,
      "annual_returns": 0.093,
      "turnover": 0.766,
      "drawdown": 0.283,
      "self_correlation": 1.0,
      "notes": "Turnover above maximum.; Self-correlation above maximum."
    }
  },
  {
    "expression": "rank(ts_delta(close,10) / ts_std_dev(close,10))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -0.66,
      "fitness": -0.32,
      "annual_returns": -0.0584,
      "turnover": 0.2504,
      "drawdown": 0.3278,
      "self_correlation": 1.0,
      "notes": "deerflow pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL"
    }
  },
  {
    "expression": "rank(ts_delta(close,60) / ts_std_dev(close,60))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -0.66,
      "fitness": -0.51,
      "annual_returns": -0.0743,
      "turnover": 0.1149,
      "drawdown": 0.4304,
      "self_correlation": 1.0,
      "notes": "WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL"
    }
  },
  {
    "expression": "rank(ts_corr(volume,returns,5))",
    "cache_used": true,
    "status": "approved",
    "gate_reasons": [],
    "metrics": {
      "sharpe": 2.215,
      "fitness": 1.728,
      "annual_returns": 0.18,
      "turnover": 0.078,
      "drawdown": 0.224,
      "self_correlation": 0.63,
      "notes": ""
    }
  },
  {
    "expression": "rank(ts_corr(volume,returns,20))",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -0.36,
      "fitness": -0.12,
      "annual_returns": -0.0162,
      "turnover": 0.1467,
      "drawdown": 0.2107,
      "self_correlation": 1.0,
      "notes": ""
    }
  },
  {
    "expression": "rank(-ts_delta(close,10))",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 1.1,
      "fitness": 0.68,
      "annual_returns": 0.0881,
      "turnover": 0.2291,
      "drawdown": 0.0681,
      "self_correlation": 1.0,
      "notes": ""
    }
  },
  {
    "expression": "rank(-ts_delta(vwap,60))",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 0.77,
      "fitness": 0.58,
      "annual_returns": 0.0721,
      "turnover": 0.0864,
      "drawdown": 0.1424,
      "self_correlation": 0.75,
      "notes": ""
    }
  },
  {
    "expression": "rank(volume / ts_mean(volume, 60))",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 0.95,
      "fitness": 0.36,
      "annual_returns": 0.0488,
      "turnover": 0.3418,
      "drawdown": 0.0874,
      "self_correlation": 1.0,
      "notes": ""
    }
  },
  {
    "expression": "rank(-ts_delta(close, 60))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 0.8,
      "fitness": 0.62,
      "annual_returns": 0.0747,
      "turnover": 0.0873,
      "drawdown": 0.1394,
      "self_correlation": 1.0,
      "notes": "WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; Sharpe below threshold.; Fitness below threshold.; Self-correlation above maximum.; hermes post-review: FAIL"
    }
  },
  {
    "expression": "rank(-ts_delta(vwap, 5))",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_FITNESS.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 1.36,
      "fitness": 0.77,
      "annual_returns": 0.1094,
      "turnover": 0.3448,
      "drawdown": 0.0705,
      "self_correlation": 1.0,
      "notes": ""
    }
  },
  {
    "expression": "rank(ts_delta(close, 5) / ts_std_dev(close, 5))",
    "cache_used": true,
    "status": "tested",
    "gate_reasons": [
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -1.12,
      "fitness": -0.57,
      "annual_returns": -0.0979,
      "turnover": 0.3771,
      "drawdown": 0.53,
      "self_correlation": 1.0,
      "notes": "deerflow pre-review: FAIL; WQ check failed: LOW_SHARPE.; WQ check failed: LOW_FITNESS.; WQ check failed: LOW_SUB_UNIVERSE_SHARPE.; Sharpe below threshold.; Fitness below threshold.; Annual returns below threshold.; Drawdown above maximum.; Self-correlation above maximum.; hermes post-review: FAIL; deerflow post-review: FAIL"
    }
  },
  {
    "expression": "rank(close / ts_mean(close, 60) - 1)",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Drawdown above maximum.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -0.62,
      "fitness": -0.51,
      "annual_returns": -0.0841,
      "turnover": 0.1006,
      "drawdown": 0.4722,
      "self_correlation": 1.0,
      "notes": ""
    }
  },
  {
    "expression": "rank(ts_corr(volume, returns, 60))",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SUB_UNIVERSE_SHARPE.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": -0.57,
      "fitness": -0.27,
      "annual_returns": -0.0275,
      "turnover": 0.0682,
      "drawdown": 0.2356,
      "self_correlation": 1.0,
      "notes": ""
    }
  },
  {
    "expression": "rank(volume / ts_mean(volume, 20))",
    "cache_used": false,
    "status": "tested",
    "gate_reasons": [
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "WQ check failed: LOW_SHARPE.",
      "WQ check failed: LOW_FITNESS.",
      "Sharpe below threshold.",
      "Fitness below threshold.",
      "Annual returns below threshold.",
      "Self-correlation above maximum."
    ],
    "metrics": {
      "sharpe": 0.75,
      "fitness": 0.22,
      "annual_returns": 0.036,
      "turnover": 0.4035,
      "drawdown": 0.1107,
      "self_correlation": 1.0,
      "notes": ""
    }
  }
]
```

## Hermes Analysis

# OWL Analysis: WorldQuant Alpha-Only Evaluation Pack

---

## 1. Strongest Candidates — Ranked and Explained

### 🥇 #1: `rank(ts_corr(volume, returns, 5))` — **APPROVED**
| Metric | Value | Verdict |
|--------|-------|---------|
| Sharpe | 2.215 | ✅ Strong |
| Fitness | 1.728 | ✅ Solid |
| Annual Returns | 0.18 | ✅ Excellent |
| Turnover | 0.078 | ✅ Very low |
| Drawdown | 0.224 | ✅ Acceptable |
| Self-correlation | 0.63 | ✅ Differentiated |

**Why it works:**
- This is a **volume-return correlation** signal — it measures whether volume and returns are moving together over a 5-day window, then ranks across the cross-section.
- Low turnover (0.078) means the signal is **stable** — the correlation structure doesn't flip day-to-day, so trading costs are minimal.
- Self-correlation of 0.63 is the **lowest in the entire pack**, meaning this alpha captures something genuinely different from the crowded momentum/reversal signals that dominate the space.
- The economic intuition is sound: stocks where volume and returns are positively correlated may be in a **trend-confirmation phase** (institutional accumulation), while negative correlation may signal distribution or noise. Ranking this captures a **flow-quality** signal.
- It passed all gate checks and is the **only approved candidate**.

---

### 🥈 #2: `rank(close / ts_mean(close, 20) - 1)` — Tested, Gated
| Metric | Value | Verdict |
|--------|-------|---------|
| Sharpe | 2.431 | ✅ Best in pack |
| Fitness | 2.201 | ✅ Best in pack |
| Annual Returns | 0.093 | ⚠️ Modest |
| Turnover | 0.766 | ❌ Too high |
| Drawdown | 0.283 | ⚠️ Elevated |
| Self-correlation | 1.0 | ❌ Maximum (crowded) |

**Why it's strong but gated:**
- This is a **20-day price momentum** signal — the percentage deviation from the 20-day moving average, ranked cross-sectionally.
- It has the **highest Sharpe and Fitness** in the pack, which means the raw predictive power is excellent.
- However, **turnover of 0.766** is extremely high — the signal is too reactive, causing excessive rebalancing. This is a design problem: the 20-day mean re-anchors every day, creating unnecessary churn.
- **Self-correlation of 1.0** means this is essentially identical to other momentum alphas already in production — it adds no diversification value.
- **Gate reasons**: Turnover above maximum, self-correlation above maximum.

**How to fix it:** Increase the lookback (e.g., 40 or 60 days), add decay smoothing, or apply truncation to reduce turnover. Consider a regime-conditional version that only fires when volatility is below a threshold.

---

### 🥉 #3: `rank(close / ts_mean(close, 5) - 1)` — Tested, Gated
| Metric | Value | Verdict |
|--------|-------|---------|
| Sharpe | 2.077 | ✅ Good |
| Fitness | 0.888 | ❌ Below threshold |
| Annual Returns | 0.111 | ✅ Decent |
| Turnover | 0.14 | ✅ Low |
| Drawdown | 0.072 | ✅ Very low |
| Self-correlation | 1.0 | ❌ Maximum (crowded) |

**Why it's mixed:**
- This is a **5-day price momentum** signal — shorter horizon than #2.
- The low turnover (0.14) and low drawdown (0.072) are attractive — it's a **clean, stable signal**.
- But fitness of 0.888 is below threshold, meaning the **risk-adjusted efficiency** isn't sufficient after costs.
- Self-correlation of 1.0 again signals crowding.
- The short 5-day lookback captures noise as much as signal, which hurts fitness.

---

## 2. Weak Candidates — Why They Fail

### Bottom 5: All Fail for the Same Core Reasons

| Expression | Sharpe | Fitness | Key Failure Mode |
|------------|--------|---------|-----------------|
| `rank(ts_mean(returns, 5))` | -1.12 | -0.67 | **Negative momentum** — betting on return persistence with a 5-day mean in a regime where short-term reversal dominates |
| `rank(ts_delta(close, 5) / ts_std_dev(close, 5))` | -1.12 | -0.57 | **Normalized 5-day momentum** — same problem, plus the normalization doesn't help in a reversal regime |
| `rank(ts_delta(close, 60) / ts_std_dev(close, 60))` | -0.66 | -0.51 | **Normalized 60-day momentum** — longer lookback but still momentum in a reversal-dominated regime |
| `rank(ts_delta(close, 10) / ts_std_dev(close, 10))` | -0.66 | -0.32 | **Normalized 10-day momentum** — intermediate lookback, same regime mismatch |
| `rank(close / ts_mean(close, 60) - 1)` | -0.62 | -0.51 | **60-day price momentum** — longest lookback, still negative |

**Why they all fail:**

1. **Regime mismatch**: The market is in a **reversal-dominated regime**. All bottom candidates are momentum signals (positive or negative), and they're all losing because the market is mean-reverting at these horizons. The reading pack explicitly notes: *"Momentum is state-dependent, not universal"* and *"Static signal definitions are fragile."*

2. **Self-correlation = 1.0 across the board**: Every single bottom candidate has maximum self-correlation. These are all variations of the same crowded trade — they're not just unprofitable, they're **redundant**.

3. **Negative Sharpe + negative Fitness**: These aren't just weak — they're **actively harmful**. They would lose money on a risk-adjusted basis.

4. **High drawdown**: The worst candidate (`rank(ts_mean(returns, 5))`) has a drawdown of 0.7134 — a 71% drawdown is catastrophic and signals extreme regime dependence.

5. **The `ts_delta / ts_std_dev` normalization doesn't help**: Normalizing by standard deviation was intended to make the signal scale-invariant and regime-robust, but it doesn't address the fundamental problem — the **direction** of the signal is wrong for the current regime.

---

## 3. Key Patterns from the Evaluation Pack

### What separates winners from losers:

| Dimension | Winners | Losers |
|-----------|---------|--------|
| **Signal type** | Volume-return correlation, price momentum | Pure return momentum, normalized momentum |
| **Turnover** | Low (0.078–0.766) | Moderate to high (0.1–0.6) |
| **Self-correlation** | 0.63–1.0 | Always 1.0 |
| **Fitness** | 1.728–2.201 | -0.67 to 0.888 |
| **Drawdown** | 0.224–0.283 | 0.327–0.713 |

### Critical insight from the reading pack:
The brute-force momentum analysis shows that `rank(ts_mean(returns, 5))` achieved Sharpe 2.448 in isolation — but in this evaluation pack, the same family structure with `ts_delta` and normalization produces **negative** results. This confirms the reading pack's warning: **momentum performance is regime-dependent**, and what worked in one period can fail in another.

---

## 4. What to Generate Next

Based on the analysis, here are the highest-priority directions:

### Priority 1: Volume-Flow Signals (following the approved winner)
The approved `rank(ts_corr(volume, returns, 5))` proves that **volume-return interaction** signals work. Explore:
- `rank(ts_corr(volume, returns, 10))` — longer horizon
- `rank(ts_corr(volume, abs(returns), 5))` — correlation with volatility, not direction
- `rank(ts_cov(volume, returns, 5))` — covariance instead of correlation
- `rank(volume / ts_mean(volume, 20) * sign(returns))` — volume surprise × return direction

**Why**: Low self-correlation, low turnover, regime-robust.

### Priority 2: Regime-Conditional Momentum
The reading pack explicitly calls for regime-aware variants:
- `rank(close / ts_mean(close, 20) - 1) * (ts_std_dev(returns, 20) < ts_std_dev(returns, 60))` — momentum only in low-volatility regimes
- `rank(close / ts_mean(close, 40) - 1)` — longer lookback to reduce turnover from the gated #2 candidate
- `rank(ts_mean(returns, 20) - ts_mean(returns, 60))` — momentum acceleration, not level

**Why**: Addresses the turnover and crowding problems that gated the strong momentum candidates.

### Priority 3: Reversal Signals (counter-regime)
Since momentum is failing, explore short-term reversal:
- `rank(-ts_delta(close, 1) / ts_std_dev(close, 20))` — 1-day reversal, normalized
- `rank(-(close / ts_mean(close, 5) - 1))` — short-term mean reversion
- `rank(-ts_zscore(close, 5))` — z-score reversal

**Why**: If the regime is reversal-dominated, these should have positive expected returns.

### Priority 4: Volatility-Normalized Signals with Low Self-Correlation
- `rank(ts_skewness(returns, 20))` — return skewness as a signal
- `rank(ts_kurtosis(returns, 20))` — tail risk signal
- `rank(ts_std_dev(returns, 5) / ts_std_dev(returns, 20))` — volatility ratio (short-term vs medium-term)

**Why**: These are structurally different from momentum, likely to have low self-correlation, and capture risk-premium effects.

### Priority 5: Price-Normalization Families (from reading pack guidance)
The reading pack says: *"When volume motifs dominate, force exploration of range, volatility, and price-normalization families."*
- `rank(high - low / ts_mean(high - low, 20))` — range normalization
- `rank((close - low) / (high - low))` — position within daily range
- `rank(close / ts_max(high, 20))` — distance from 20-day high

---

## 5. Summary

| Rank | Expression | Status | Action |
|------|-----------|--------|--------|
| 1 | `rank(ts_corr(volume, returns, 5))` | ✅ Approved | **Submit** — low turnover, low self-correlation, strong metrics |
| 2 | `rank(close / ts_mean(close, 20) - 1)` | ⚠️ Gated | Fix turnover (longer lookback, decay) and reduce self-correlation |
| 3 | `rank(close / ts_mean(close, 5) - 1)` | ⚠️ Gated | Improve fitness (longer lookback or add conditioning) |
| 4-8 | All bottom candidates | ❌ Rejected | Abandon — wrong regime, crowded, negative risk-adjusted returns |

**The single most important takeaway**: The approved alpha succeeds because it's **not a pure momentum signal** — it's a **volume-return correlation** signal with low turnover and low self-correlation. The reading pack's guidance is validated: *"A weaker but lower self-correlation alpha may still be more useful than another crowded winner."* Future generation should prioritize **flow-quality, regime-conditional, and structurally novel** signals over variations of price momentum.

## DeerFlow Analysis

# OWL Analysis: WorldQuant Alpha-Only Evaluation Pack

---

## 1. Strongest Candidates

### 🥇 `rank(ts_corr(volume, returns, 5))` — **APPROVED**
| Metric | Value | Verdict |
|--------|-------|---------|
| Sharpe | 2.215 | ✅ Strong |
| Fitness | 1.728 | ✅ Solid |
| Turnover | 0.078 | ✅ Excellent |
| Drawdown | 0.224 | ✅ Controlled |
| Self-correlation | 0.63 | ✅ Differentiated |

**Why it works:** This is a *cross-sectional correlation* signal — it ranks stocks by how tightly their recent volume and returns move together over a 5-day window. This captures a fundamentally different mechanism than pure price momentum. It's essentially measuring **volume-confirmed momentum** or **informed flow**: stocks where price moves are accompanied by volume participation tend to have more persistent trends. The low turnover (0.078) means the signal is stable — the correlation structure doesn't flip day-to-day. The self-correlation of 0.63 is the lowest in the entire pack, meaning this alpha is **genuely differentiated** from the crowded momentum clones that dominate the rest of the set. This is exactly the kind of signal the reading pack says to reward: slightly lower Sharpe than the best momentum variant, but far more unique and cost-efficient.

---

### 🥈 `rank(close / ts_mean(close, 20) - 1)` — Tested (Gated)
| Metric | Value | Verdict |
|--------|-------|---------|
| Sharpe | 2.431 | ✅ Best in pack |
| Fitness | 2.201 | ✅ Best in pack |
| Turnover | 0.766 | ❌ Too high |
| Self-correlation | 1.0 | ❌ Fully crowded |

**Why it's gated despite top metrics:** This is a classic **20-day price momentum** signal — rank stocks by their percentage deviation from their 20-day moving average. It has the highest raw Sharpe and fitness in the pack, but it fails on two critical gates: turnover of 0.766 is far above the maximum (likely ~0.3–0.4), and self-correlation of 1.0 means it's perfectly correlated with existing signals in the book. The reading pack explicitly warns: *"A weaker but lower self-correlation alpha may still be more useful than another crowded winner."* This is that textbook case. The high turnover comes from the short lookback relative to the signal's sensitivity — small price changes cause large rank reshufflings.

**How to fix it:** Per the reading pack's guidance — increase decay, extend lookback, or add truncation. A variant like `rank(close / ts_mean(close, 40) - 1)` with higher decay could preserve the momentum hypothesis while reducing turnover and self-correlation.

---

### 🥉 `rank(close / ts_mean(close, 5) - 1)` — Tested (Gated)
| Metric | Value | Verdict |
|--------|-------|---------|
| Sharpe | 2.077 | ✅ Good |
| Fitness | 0.888 | ❌ Below threshold |
| Turnover | 0.14 | ✅ Low |
| Self-correlation | 1.0 | ❌ Fully crowded |

**Why it fails:** This is a **5-day momentum** signal. The short lookback makes it noisy — hence the low fitness (0.888) despite decent Sharpe. The reading pack notes that short horizons cause noisy signals. The self-correlation of 1.0 again confirms this is a crowded momentum variant. The brute-force research context shows that `rank(ts_mean(returns, 5))` achieved Sharpe 2.448 with fitness 1.926, so the *returns-based* 5-day momentum is stronger than the *price-deviation* version. This suggests the `close / ts_mean(close, 5) - 1` formulation introduces noise that `ts_mean(returns, 5)` avoids.

---

## 2. Why the Bottom Candidates Fail

Every single bottom candidate shares the same fatal pattern: **negative Sharpe, negative fitness, and self-correlation of 1.0**. They are all *short-term reversal signals disguised as momentum* — or more precisely, they are **momentum signals with the wrong sign**.

### The Common Failure Mode

| Expression | Sharpe | Core Problem |
|-----------|--------|-------------|
| `rank(ts_mean(returns, 5))` | -1.12 | Positive return mean → this IS momentum, but the sign is wrong in the current regime |
| `rank(ts_delta(close, 5) / ts_std_dev(close, 5))` | -1.12 | Normalized 5-day price change → momentum with wrong sign |
| `rank(ts_delta(close, 60) / ts_std_dev(close, 60))` | -0.66 | Normalized 60-day price change → longer lookback, same sign problem |
| `rank(ts_delta(close, 10) / ts_std_dev(close, 10))` | -0.66 | Normalized 10-day price change → same issue |
| `rank(close / ts_mean(close, 60) - 1)` | -0.62 | 60-day price deviation → same sign problem |

**The reading pack's market regime notes explain this perfectly:** *"Momentum is state-dependent, not universal"* and *"momentum can crash when liquidity conditions change or market rebounds begin."* The negative returns across all lookbacks (5, 10, 60) suggest the test period captured a **reversal regime** where recent winners became losers. These formulas are structurally identical to the top candidates — they're just pointing the wrong direction for the current regime.

**Additional failure modes:**
- **Drawdown above maximum** (0.33–0.71): These signals are not just unprofitable — they're *dangerously* concentrated. The reading pack notes that large drawdown means the alpha is too regime-dependent.
- **Self-correlation of 1.0**: Even the failed signals are perfectly correlated with the approved book, meaning they add nothing new.
- **The `ts_std_dev` normalization doesn't help**: Dividing by volatility doesn't fix the fundamental sign problem. It just scales the noise.

---

## 3. Structural Patterns Across the Pack

### What Works
1. **Cross-sectional correlation** (`ts_corr`) between different data types (volume × returns) — this is the only truly differentiated signal
2. **Price deviation from moving average** with moderate lookback (20-day) — strong but crowded
3. **Low turnover + low self-correlation** combination — the approved candidate proves this trade-off is worth making

### What Fails
1. **Normalized price delta** (`ts_delta / ts_std_dev`) — fails at every lookback
2. **Simple return averaging** with positive sign in a reversal regime
3. **Any signal with self-correlation of 1.0** — perfectly crowded, no marginal value
4. **Short-horizon price deviation** (5-day) — too noisy for the fitness threshold

---

## 4. What to Generate Next

Based on the reading pack's guidance and the gaps in this evaluation, here are the highest-priority directions:

### Priority 1: Regime-Aware Momentum Variants
The reading pack explicitly says: *"Prefer regime-aware variants of momentum instead of one fixed ranking rule across all states."*

- `rank(ts_corr(volume, returns, 10))` — extend the approved signal's lookback for stability
- `rank(ts_corr(volume, returns, 20))` — test if longer correlation windows improve turnover further
- `rank(if_else(volume > ts_mean(volume, 20), close / ts_mean(close, 20) - 1, 0))` — momentum only when volume confirms

### Priority 2: Volume-Price Divergence Signals
The approved signal uses volume-return *correlation*. The next frontier is *divergence*:

- `rank(ts_corr(volume, returns, 5) - ts_corr(volume, returns, 20))` — short-term vs long-term volume-price alignment
- `rank(volume / ts_mean(volume, 20) - close / ts_mean(close, 20))` — volume momentum minus price momentum

### Priority 3: Fix the Gated 20-Day Momentum
Per the reading pack: *"If turnover is too high, try higher decay or longer lookback before discarding the hypothesis."*

- `rank(close / ts_mean(close, 40) - 1)` — extend lookback to reduce turnover
- `rank(ts_decay_linear(close / ts_mean(close, 20) - 1, 10))` — add decay to stabilize ranks
- `rank(ts_mean(returns, 20))` — use returns-based momentum instead of price deviation (the brute-force data shows this has Sharpe 1.585 with better turnover characteristics)

### Priority 4: Non-Price Data Families
The reading pack says: *"When volume motifs dominate, force exploration of range, volatility, and price-normalization families."*

- `rank(high - low / ts_mean(high - low, 20))` — range-based volatility signal
- `rank(ts_std_dev(returns, 5) / ts_std_dev(returns, 20))` — short-term vs long-term volatility ratio
- `rank(-ts_skewness(returns, 20))` — negative skewness as a risk signal

### Priority 5: Conditional/Reversal-Aware Signals
Since the bottom candidates show the current regime punishes naive momentum:

- `rank(-ts_delta(close, 5) * ts_corr(volume, returns, 5))` — reversal signal weighted by volume confirmation
- `rank(if_else(close < ts_mean(close, 20), ts_delta(close, 5), 0))` — mean-reversion below the moving average

---

## Summary

| Rank | Expression | Key Lesson |
|------|-----------|------------|
| 1 | `rank(ts_corr(volume, returns, 5))` | Cross-asset-type correlation is the only differentiated signal |
| 2 | `rank(close / ts_mean(close, 20) - 1)` | Strongest raw metrics but gated — needs turnover fix |
| 3 | `rank(close / ts_mean(close, 5) - 1)` | Too short, too noisy — extend lookback |
| Bottom 5 | All `ts_delta/std_dev` and `ts_mean(returns)` | Wrong sign for current regime + fully crowded |

**The single most important takeaway:** The only approved signal in this entire pack is the one that measures something *different* — volume-return correlation rather than pure price momentum. Every other formula, whether top or bottom, is a variation on the same crowded momentum theme. The next generation of formulas should prioritize **cross-data-type signals**, **regime conditioning**, and **lower self-correlation** over raw Sharpe optimization.
