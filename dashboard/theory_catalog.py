from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any


THEORY_CATALOG: list[dict[str, Any]] = [
    {
        "id": "econ-emh-violations",
        "domain": "Economics",
        "title": "EMH Violations",
        "sector_tags": ["Multi-sector", "Large Cap", "Broad Market"],
        "core_principle": "Prices do not always instantaneously absorb information, so temporary mispricings can persist long enough to trade.",
        "alpha_implication": [
            "Look for delayed reactions in price or liquidity.",
            "Prefer robust cross-sectional ranking instead of raw levels.",
        ],
        "example_expression": "rank(close / ts_mean(close, 20) - 1)",
        "agent_reasoning": [
            "If the market underreacts, medium-horizon price-vs-mean gaps can stay open.",
            "Ranking the gap turns the theory into a tradable relative-value signal.",
            "The agent prefers 20-day windows because they often improve fitness over very short horizons.",
        ],
    },
    {
        "id": "econ-ff5",
        "domain": "Economics",
        "title": "Fama-French 5 Factors",
        "sector_tags": ["Financials", "Industrials", "Quality", "Value"],
        "core_principle": "Expected returns are partly explained by systematic exposures such as size, value, profitability, and investment intensity.",
        "alpha_implication": [
            "Translate factor tilts into normalized relative signals.",
            "Use neutralization to separate stock-specific alpha from sector beta.",
        ],
        "example_expression": "rank(close / ts_mean(close, 60) - 1)",
        "agent_reasoning": [
            "Without full fundamental fields in the safe generator, the agent uses slower price structure as a proxy for persistent factor drift.",
            "A long lookback helps approximate gradual factor repricing rather than short noise.",
        ],
    },
    {
        "id": "econ-apt",
        "domain": "Economics",
        "title": "Arbitrage Pricing Theory",
        "sector_tags": ["Macro-sensitive", "Rates", "Cyclicals"],
        "core_principle": "Returns reflect multiple latent risk premia rather than a single market factor.",
        "alpha_implication": [
            "Diversify alpha families so each captures a different latent risk source.",
            "Avoid near-duplicate expressions with identical economic intuition.",
        ],
        "example_expression": "rank(ts_corr(volume, returns, 20))",
        "agent_reasoning": [
            "A volume-return interaction can capture a different channel than price trend alone.",
            "The agent maps APT to family diversification rather than one formula only.",
        ],
    },
    {
        "id": "econ-microstructure",
        "domain": "Economics",
        "title": "Market Microstructure",
        "sector_tags": ["Small Cap", "High Turnover", "Liquidity"],
        "core_principle": "Short-term returns are affected by order flow, spread dynamics, and inventory pressure.",
        "alpha_implication": [
            "Use turnover-aware designs and avoid signals that rebalance too aggressively.",
            "Volume-confirmation motifs can encode order-flow pressure.",
        ],
        "example_expression": "rank(ts_corr(volume, returns, 5))",
        "agent_reasoning": [
            "If rising volume confirms return direction, order flow may still be pushing price.",
            "The agent keeps the operator simple but interprets it through microstructure logic.",
        ],
    },
    {
        "id": "econ-liquidity-premium",
        "domain": "Economics",
        "title": "Liquidity Premium",
        "sector_tags": ["Small Cap", "Financials", "Energy"],
        "core_principle": "Less liquid assets may command higher expected returns, but liquidity shocks can also drive short-term dislocations.",
        "alpha_implication": [
            "Use liquidity as both a signal and a risk-control dimension.",
            "Prefer slower horizons when volume ratios become noisy.",
        ],
        "example_expression": "rank(volume / ts_mean(volume, 20))",
        "agent_reasoning": [
            "A sustained liquidity regime shift can matter more than a one-day spike.",
            "The agent extends lookback to reduce false positives and improve fitness.",
        ],
    },
    {
        "id": "beh-overreaction",
        "domain": "Behavioral",
        "title": "Overreaction and Mean Reversion",
        "sector_tags": ["Consumer", "High Beta", "Retail Flow"],
        "core_principle": "Investors can overshoot on recent news, causing short-horizon reversals.",
        "alpha_implication": [
            "Negative recent returns can become long candidates in reversal setups.",
            "Smoothing recent returns often improves robustness.",
        ],
        "example_expression": "rank(-ts_delta(close, 10))",
        "agent_reasoning": [
            "The minus sign encodes the bounce-back thesis.",
            "The agent avoids single-day reversal and uses a 10-day delta to reduce noise.",
        ],
    },
    {
        "id": "beh-underreaction",
        "domain": "Behavioral",
        "title": "Momentum and Underreaction",
        "sector_tags": ["Technology", "Growth", "Semiconductors"],
        "core_principle": "Information can diffuse gradually, producing trend persistence rather than instant repricing.",
        "alpha_implication": [
            "Use continuation structures on medium horizons.",
            "Prefer volatility-normalized trend over raw price change when noise is high.",
        ],
        "example_expression": "rank(ts_delta(close, 20) / ts_std_dev(close, 20))",
        "agent_reasoning": [
            "A volatility-normalized move separates genuine continuation from random swings.",
            "The agent treats this as a fitness-first momentum motif.",
        ],
    },
    {
        "id": "beh-prospect-theory",
        "domain": "Behavioral",
        "title": "Prospect Theory and Loss Aversion",
        "sector_tags": ["Panic Selling", "Defensives", "Utilities"],
        "core_principle": "Investors weigh losses more heavily than gains, often creating asymmetric reactions after drawdowns.",
        "alpha_implication": [
            "Look for rebound setups after concentrated negative moves.",
            "Be careful during broad market stress because reversal can break.",
        ],
        "example_expression": "rank(-ts_delta(vwap, 5))",
        "agent_reasoning": [
            "VWAP-based reversal uses a price anchor closer to traded flow than close alone.",
            "The agent chooses a short horizon because panic overshoots are often brief.",
        ],
    },
    {
        "id": "beh-anchoring",
        "domain": "Behavioral",
        "title": "Anchoring Bias",
        "sector_tags": ["Earnings", "Event-driven", "Large Cap"],
        "core_principle": "Investors anchor on stale reference points and adjust too slowly when new information arrives.",
        "alpha_implication": [
            "Relative distance from a rolling mean can capture incomplete adjustment.",
            "Anchors work best when compared cross-sectionally.",
        ],
        "example_expression": "rank(close / ts_mean(close, 20) - 1)",
        "agent_reasoning": [
            "The moving average is treated as a soft anchor.",
            "Stocks far from the anchor may still be repricing.",
        ],
    },
    {
        "id": "beh-herding",
        "domain": "Behavioral",
        "title": "Herding Behavior",
        "sector_tags": ["Momentum Crowding", "Social Flow", "Thematic Baskets"],
        "core_principle": "Investors often chase the same names, creating crowded trends and crowded reversals.",
        "alpha_implication": [
            "Use self-correlation as an explicit penalty.",
            "Avoid cloning the same short-horizon volume idea repeatedly.",
        ],
        "example_expression": "rank(ts_corr(volume, returns, 20))",
        "agent_reasoning": [
            "Volume can reveal crowded participation.",
            "The agent pairs herding theory with uniqueness checks before submission.",
        ],
    },
    {
        "id": "math-linear-factor",
        "domain": "Mathematics",
        "title": "Linear Factor Decomposition",
        "sector_tags": ["Portfolio Construction", "Cross-sectional"],
        "core_principle": "Returns can be decomposed into systematic and idiosyncratic components through linear factor structure.",
        "alpha_implication": [
            "Neutralization is a practical proxy for removing systematic drift.",
            "Compare families that explain different residual structures.",
        ],
        "example_expression": "rank(ts_mean(returns, 20))",
        "agent_reasoning": [
            "Residual continuation can survive even after broad neutralization.",
            "The agent uses decomposition logic to justify sector-neutral ranking.",
        ],
    },
    {
        "id": "math-ou",
        "domain": "Mathematics",
        "title": "Ornstein-Uhlenbeck Mean Reversion",
        "sector_tags": ["Range-bound", "Defensives", "Relative Value"],
        "core_principle": "A mean-reverting process tends to drift back toward equilibrium after displacement.",
        "alpha_implication": [
            "Use price displacement from a local mean or recent path.",
            "Prefer reversal only when market regime is not strongly trending.",
        ],
        "example_expression": "rank(-(close / ts_mean(close, 20) - 1))",
        "agent_reasoning": [
            "The expression treats rolling mean as local equilibrium.",
            "The agent reverses the deviation to bet on snapback.",
        ],
    },
    {
        "id": "math-zscore",
        "domain": "Mathematics",
        "title": "Z-score Normalization",
        "sector_tags": ["Cross-sectional", "Risk Control", "Normalization"],
        "core_principle": "Normalization rescales features so they are comparable across names and time.",
        "alpha_implication": [
            "When z-score is unavailable or risky, rank is a safer robustness proxy.",
            "Normalization usually improves signal comparability.",
        ],
        "example_expression": "rank(ts_delta(close, 20) / ts_std_dev(close, 20))",
        "agent_reasoning": [
            "Dividing by rolling volatility creates a local normalization.",
            "The agent substitutes rank plus volatility scaling for a raw z-score.",
        ],
    },
    {
        "id": "math-correlation-decomp",
        "domain": "Mathematics",
        "title": "Correlation Decomposition",
        "sector_tags": ["Liquidity", "Crowding", "Flow"],
        "core_principle": "Correlation can capture shared movement between return and participation, not just direction.",
        "alpha_implication": [
            "Volume-return correlation can serve as a flow-sensitive alpha family.",
            "Different lookbacks can separate tactical flow from structural participation.",
        ],
        "example_expression": "rank(ts_corr(volume, returns, 20))",
        "agent_reasoning": [
            "The agent interprets correlation as an interaction term rather than a raw factor.",
            "Longer windows often help fitness when short correlation is noisy.",
        ],
    },
    {
        "id": "math-time-series-ops",
        "domain": "Mathematics",
        "title": "Time-series Operators",
        "sector_tags": ["All Sectors", "Signal Design", "Robustness"],
        "core_principle": "Operators such as rolling mean, delta, standard deviation, and correlation transform raw fields into structured hypotheses.",
        "alpha_implication": [
            "Operator choice is equivalent to choosing a hypothesis class.",
            "Short operators increase sensitivity; long operators increase stability.",
        ],
        "example_expression": "rank(ts_mean(returns, 60))",
        "agent_reasoning": [
            "The agent searches over operator families, not just formulas.",
            "Time-series smoothing is one of the cleanest ways to target higher fitness.",
        ],
    },
    {
        "id": "stat-fama-macbeth",
        "domain": "Statistics",
        "title": "Fama-MacBeth Regression",
        "sector_tags": ["Cross-sectional", "Factor Testing", "Style Factors"],
        "core_principle": "Cross-sectional regressions estimate whether characteristics explain returns consistently across time.",
        "alpha_implication": [
            "Rank-based alphas approximate a cross-sectional signal sort.",
            "Repeated pass/fail behavior across runs is evidence about stability.",
        ],
        "example_expression": "rank(ts_mean(returns, 20))",
        "agent_reasoning": [
            "The agent treats each simulation as a panel-data test of a ranked characteristic.",
            "Cross-run consistency matters as much as single-run Sharpe.",
        ],
    },
    {
        "id": "stat-order-statistics",
        "domain": "Statistics",
        "title": "Order Statistics and Ranking",
        "sector_tags": ["Cross-sectional", "Portfolio Sorting", "Outlier Control"],
        "core_principle": "Rank transforms noisy magnitudes into stable order information and reduces outlier sensitivity.",
        "alpha_implication": [
            "Wrap most signals in rank when raw scale is unstable.",
            "Ranking is especially useful for broad universes such as TOP3000.",
        ],
        "example_expression": "rank(volume / ts_mean(volume, 20))",
        "agent_reasoning": [
            "The raw ratio may be unstable, but rank keeps the relative ordering.",
            "The agent uses rank as a default robustness layer.",
        ],
    },
    {
        "id": "stat-garch",
        "domain": "Statistics",
        "title": "GARCH and Volatility Clustering",
        "sector_tags": ["Volatility", "Risk Regime", "Macro Stress"],
        "core_principle": "Volatility tends to cluster, so risk conditions are state-dependent rather than constant.",
        "alpha_implication": [
            "Normalize directional signals by rolling volatility.",
            "Expect reversal strategies to behave differently in high-volatility states.",
        ],
        "example_expression": "rank(ts_delta(close, 20) / ts_std_dev(close, 20))",
        "agent_reasoning": [
            "Volatility scaling is a lightweight way to respect clustered risk.",
            "The agent prefers this motif when raw momentum is too unstable.",
        ],
    },
    {
        "id": "stat-winsorization",
        "domain": "Statistics",
        "title": "Winsorization and Truncation",
        "sector_tags": ["Risk Control", "Concentration", "Portfolio Construction"],
        "core_principle": "Extreme exposures can dominate a portfolio unless they are capped or truncated.",
        "alpha_implication": [
            "Truncation protects against concentration and unstable tails.",
            "A high-Sharpe idea can still fail if drawdown or concentration is too high.",
        ],
        "example_expression": "rank(close / ts_mean(close, 20) - 1)",
        "agent_reasoning": [
            "The agent maps this theory to simulation settings as much as to formula design.",
            "It justifies truncation when a price-dislocation signal becomes too concentrated.",
        ],
    },
    {
        "id": "info-ir",
        "domain": "Information Theory",
        "title": "Information Ratio and Signal Quality",
        "sector_tags": ["Evaluation", "IC", "Cross-sectional"],
        "core_principle": "A useful signal should produce consistent predictive information, not only occasional wins.",
        "alpha_implication": [
            "Optimize for repeatable risk-adjusted performance.",
            "Fitness-first generation is a practical proxy for signal efficiency.",
        ],
        "example_expression": "rank(ts_corr(volume, returns, 5))",
        "agent_reasoning": [
            "The agent prefers motifs that keep predictive structure while controlling turnover.",
            "A signal with lower raw Sharpe can still win if its efficiency is better.",
        ],
    },
    {
        "id": "info-entropy",
        "domain": "Information Theory",
        "title": "Shannon Entropy and Mutual Information",
        "sector_tags": ["Feature Selection", "Novelty", "Crowding"],
        "core_principle": "Signals are valuable when they encode information that is not redundant with what is already known.",
        "alpha_implication": [
            "Penalize duplicate formulas and high self-correlation.",
            "Broaden the operator family when the current pool becomes repetitive.",
        ],
        "example_expression": "rank(-ts_delta(vwap, 5))",
        "agent_reasoning": [
            "Switching from close to VWAP can add informational variety.",
            "The agent interprets novelty as part of the objective, not just a side effect.",
        ],
    },
    {
        "id": "info-accruals",
        "domain": "Information Theory",
        "title": "Accruals Anomaly",
        "sector_tags": ["Accounting", "Industrials", "Healthcare", "Value"],
        "core_principle": "Lower-quality earnings components tend to be mispriced relative to cash-flow quality.",
        "alpha_implication": [
            "When richer data fields are available, use accounting quality as a slow-moving low-turnover source.",
            "In the safe operator set, the lesson is to prefer slower, more persistent information channels.",
        ],
        "example_expression": "rank(ts_mean(returns, 60))",
        "agent_reasoning": [
            "The current safe generator cannot express accrual fields directly.",
            "The agent still uses the anomaly as a cue to search for slower, more durable signals.",
        ],
    },
]


def theory_domains(catalog: list[dict[str, Any]] | None = None) -> list[str]:
    items = catalog or THEORY_CATALOG
    return sorted({item["domain"] for item in items})


def theory_sector_tags(catalog: list[dict[str, Any]] | None = None) -> list[str]:
    items = catalog or THEORY_CATALOG
    tags: set[str] = set()
    for item in items:
        tags.update(item["sector_tags"])
    return sorted(tags)


def build_standalone_html(output_path: str | Path, catalog: list[dict[str, Any]] | None = None) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    items = catalog or THEORY_CATALOG
    data_json = json.dumps(items, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>WQ Brain Theory Explorer</title>
  <style>
    :root {{
      --bg: #0d1b1e;
      --panel: #12262a;
      --panel-soft: #173238;
      --text: #edf6f4;
      --muted: #9fc0bb;
      --accent: #e6a83c;
      --good: #5bc58f;
      --border: rgba(255,255,255,0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", system-ui, sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top right, rgba(230,168,60,0.18), transparent 28%),
        linear-gradient(180deg, #0a1517 0%, var(--bg) 100%);
      min-height: 100vh;
    }}
    .shell {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.4fr 0.6fr;
      gap: 20px;
      margin-bottom: 24px;
    }}
    .hero-card, .filter-card, .theory-card {{
      background: rgba(18,38,42,0.88);
      border: 1px solid var(--border);
      border-radius: 20px;
      box-shadow: 0 18px 50px rgba(0,0,0,0.22);
    }}
    .hero-card {{
      padding: 28px;
    }}
    .eyebrow {{
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 12px;
      margin-bottom: 8px;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 40px;
      line-height: 1.05;
    }}
    .hero p {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
      line-height: 1.65;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
    }}
    .stat {{
      padding: 20px;
      border-radius: 18px;
      background: var(--panel-soft);
      border: 1px solid var(--border);
    }}
    .stat .value {{
      font-size: 34px;
      font-weight: 700;
      margin-bottom: 4px;
    }}
    .stat .label {{
      color: var(--muted);
      font-size: 13px;
    }}
    .filters {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .filter-card {{
      padding: 16px;
    }}
    label {{
      display: block;
      margin-bottom: 8px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    select, input {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: rgba(8,18,20,0.72);
      color: var(--text);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 18px;
    }}
    .theory-card {{
      padding: 20px;
    }}
    .meta {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin: 12px 0 14px;
    }}
    .pill {{
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(230,168,60,0.12);
      border: 1px solid rgba(230,168,60,0.25);
      color: #ffd38d;
      font-size: 12px;
    }}
    details {{
      margin-top: 14px;
      border-top: 1px solid var(--border);
      padding-top: 14px;
    }}
    summary {{
      cursor: pointer;
      color: var(--good);
      font-weight: 600;
      list-style: none;
    }}
    summary::-webkit-details-marker {{ display: none; }}
    .section-title {{
      margin: 18px 0 8px;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.55;
    }}
    code {{
      display: block;
      white-space: pre-wrap;
      padding: 14px;
      border-radius: 14px;
      background: rgba(6,13,14,0.88);
      border: 1px solid var(--border);
      color: #eaf7f5;
      line-height: 1.6;
      font-size: 13px;
    }}
    .op {{ color: #7be0b4; }}
    .field {{ color: #ffcf72; }}
    .num {{ color: #c9a0ff; }}
    .muted {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.6;
    }}
    .empty {{
      display: none;
      padding: 28px;
      text-align: center;
      color: var(--muted);
    }}
    @media (max-width: 920px) {{
      .hero {{ grid-template-columns: 1fr; }}
      .filters {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media (max-width: 640px) {{
      .filters {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 30px; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="hero-card">
        <div class="eyebrow">WQ Brain Theory Explorer</div>
        <h1>22 theories mapped to alpha expression design.</h1>
        <p>
          Filter by domain, sector relevance, or keyword. Each card expands into
          four layers: core principle, alpha implication, sample expression, and
          the agent reasoning chain from theory to code.
        </p>
      </div>
      <div class="stats">
        <div class="stat"><div class="value">22</div><div class="label">theories</div></div>
        <div class="stat"><div class="value">5</div><div class="label">domains</div></div>
        <div class="stat"><div class="value">4</div><div class="label">detail layers per card</div></div>
        <div class="stat"><div class="value">HTML</div><div class="label">standalone export</div></div>
      </div>
    </section>

    <section class="filters">
      <div class="filter-card">
        <label for="domainFilter">Domain</label>
        <select id="domainFilter"></select>
      </div>
      <div class="filter-card">
        <label for="sectorFilter">Sector / relevance</label>
        <select id="sectorFilter"></select>
      </div>
      <div class="filter-card">
        <label for="searchInput">Search</label>
        <input id="searchInput" placeholder="Search theory, alpha motif, sector..." />
      </div>
      <div class="filter-card">
        <label>Visible cards</label>
        <div id="visibleCount" style="font-size:28px;font-weight:700;">0</div>
        <div class="muted">cards match current filters</div>
      </div>
    </section>

    <div id="cardGrid" class="grid"></div>
    <div id="emptyState" class="empty">No theory cards matched the current filters.</div>
  </div>

  <script>
    const catalog = {data_json};
    const domainFilter = document.getElementById("domainFilter");
    const sectorFilter = document.getElementById("sectorFilter");
    const searchInput = document.getElementById("searchInput");
    const cardGrid = document.getElementById("cardGrid");
    const emptyState = document.getElementById("emptyState");
    const visibleCount = document.getElementById("visibleCount");

    function highlightExpression(expression) {{
      const operatorPattern = /(rank|ts_mean|ts_delta|ts_std_dev|ts_corr|zscore)/g;
      const fieldPattern = /(returns|close|volume|vwap|cap|adv20|pb)/g;
      const numberPattern = /(\\b\\d+(?:\\.\\d+)?\\b)/g;
      return expression
        .replace(operatorPattern, '<span class="op">$1</span>')
        .replace(fieldPattern, '<span class="field">$1</span>')
        .replace(numberPattern, '<span class="num">$1</span>');
    }}

    function optionMarkup(values) {{
      return ['<option value="All">All</option>'].concat(values.map((value) => `<option value="${{value}}">${{value}}</option>`)).join('');
    }}

    function renderCard(item) {{
      const sectors = item.sector_tags.map((tag) => `<span class="pill">${{tag}}</span>`).join('');
      const implications = item.alpha_implication.map((point) => `<li>${{point}}</li>`).join('');
      const reasoning = item.agent_reasoning.map((point) => `<li>${{point}}</li>`).join('');
      return `
        <article class="theory-card" data-domain="${{item.domain}}" data-sectors="${{item.sector_tags.join('|')}}" data-search="${{(item.title + ' ' + item.domain + ' ' + item.core_principle + ' ' + item.sector_tags.join(' ')).toLowerCase()}}">
          <div class="eyebrow">${{item.domain}}</div>
          <h3 style="margin:0 0 8px;">${{item.title}}</h3>
          <div class="muted">${{item.core_principle}}</div>
          <div class="meta">${{sectors}}</div>
          <details>
            <summary>Open theory card</summary>
            <div class="section-title">Core Principle</div>
            <div class="muted">${{item.core_principle}}</div>
            <div class="section-title">Alpha Implication</div>
            <ul>${{implications}}</ul>
            <div class="section-title">Example Expression</div>
            <code>${{highlightExpression(item.example_expression)}}</code>
            <div class="section-title">Agent Reasoning Chain</div>
            <ul>${{reasoning}}</ul>
          </details>
        </article>
      `;
    }}

    function render() {{
      const selectedDomain = domainFilter.value;
      const selectedSector = sectorFilter.value;
      const query = searchInput.value.trim().toLowerCase();
      let visible = 0;
      const markup = catalog.filter((item) => {{
        const domainOk = selectedDomain === 'All' || item.domain === selectedDomain;
        const sectorOk = selectedSector === 'All' || item.sector_tags.includes(selectedSector);
        const searchBlob = (item.title + ' ' + item.domain + ' ' + item.core_principle + ' ' + item.alpha_implication.join(' ') + ' ' + item.agent_reasoning.join(' ') + ' ' + item.sector_tags.join(' ')).toLowerCase();
        const queryOk = !query || searchBlob.includes(query);
        return domainOk && sectorOk && queryOk;
      }}).map((item) => {{
        visible += 1;
        return renderCard(item);
      }}).join('');

      visibleCount.textContent = String(visible);
      cardGrid.innerHTML = markup;
      emptyState.style.display = visible === 0 ? 'block' : 'none';
    }}

    const domains = [...new Set(catalog.map((item) => item.domain))].sort();
    const sectors = [...new Set(catalog.flatMap((item) => item.sector_tags))].sort();
    domainFilter.innerHTML = optionMarkup(domains);
    sectorFilter.innerHTML = optionMarkup(sectors);
    domainFilter.addEventListener('change', render);
    sectorFilter.addEventListener('change', render);
    searchInput.addEventListener('input', render);
    render();
  </script>
</body>
</html>
"""
    output.write_text(html, encoding="utf-8")
    return output


def build_theory_card_markdown(item: dict[str, Any]) -> str:
    principles = "".join(f"<li>{escape(point)}</li>" for point in item["alpha_implication"])
    reasoning = "".join(f"<li>{escape(point)}</li>" for point in item["agent_reasoning"])
    return (
        f"<div style='padding:18px;border:1px solid rgba(255,255,255,0.08);"
        f"border-radius:18px;background:rgba(13,27,30,0.64);'>"
        f"<div style='font-size:12px;letter-spacing:0.08em;text-transform:uppercase;color:#d2a95c;'>"
        f"{escape(item['domain'])}</div>"
        f"<div style='font-size:24px;font-weight:700;margin:6px 0 10px;'>{escape(item['title'])}</div>"
        f"<div style='color:#aac3be;line-height:1.6;'>{escape(item['core_principle'])}</div>"
        f"<div style='margin:12px 0 0;color:#9fc0bb;font-size:12px;text-transform:uppercase;'>Alpha implication</div>"
        f"<ul style='color:#edf6f4;line-height:1.5;margin-top:8px;'>{principles}</ul>"
        f"<div style='margin:12px 0 8px;color:#9fc0bb;font-size:12px;text-transform:uppercase;'>Example expression</div>"
        f"<pre style='white-space:pre-wrap;padding:12px;border-radius:12px;background:#081214;color:#edf6f4;border:1px solid rgba(255,255,255,0.08);'>{escape(item['example_expression'])}</pre>"
        f"<div style='margin:12px 0 8px;color:#9fc0bb;font-size:12px;text-transform:uppercase;'>Agent reasoning chain</div>"
        f"<ul style='color:#edf6f4;line-height:1.5;'>{reasoning}</ul>"
        f"</div>"
    )
