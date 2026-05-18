# System Gap Analysis

Updated: `2026-05-18`
Scope: qualitative review of `Alpha_Generator` against practical operator needs and recent alpha-system patterns

## 1. Overall Assessment

`Alpha_Generator` already has a strong architectural base:
- multi-source alpha generation,
- Hermes and DeerFlow review before and after simulation,
- structured quality gate,
- persisted workflow events,
- alpha explainability layer,
- human-in-the-loop Studio.

The current maturity level is:
- operational,
- inspectable,
- partially explainable,
- but not yet deeply observable or self-reflective.

In short:
- the system can run,
- the system can persist,
- the system can explain results,
- but the system still cannot measure its own quality trajectory well enough to improve automatically with confidence.

## 2. UI Analysis

### 2.1 Biggest usability issue

The largest UI weakness is lack of real-time feedback.

Current state:
- Dashboard uses polling
- Logs use polling
- Studio chat is request-response, not token streaming

Impact:
- long pipeline runs feel stale,
- operators cannot tell whether the system is slow or stuck,
- agent interaction feels less responsive than the backend architecture deserves.

### 2.2 Alpha Detail weakness

Alpha Detail is still fragile at the moment an alpha is first created.

Current gaps:
- no skeleton state,
- no explicit explanation-pending state,
- no on-demand explanation generation trigger,
- blank or thin sections can appear if explanation is not ready yet.

Impact:
- this is the exact moment when operator curiosity is highest,
- but the page gives the weakest feedback there.

### 2.3 Studio weakness

Studio is useful, but state management is still lightweight.

Current issues:
- chatspace is stored in local browser storage only,
- candidate pool UX is still basic,
- there is no strong lifecycle around candidate add, undo, promote, reject, or archive.

Impact:
- Studio works for experimentation,
- but it is not yet a robust research workstation.

## 3. Backend Reflection Gaps

This is the most important systems gap for long-term alpha iteration quality.

### 3.1 Missing tracking fields

The system still lacks several fields that would let agents reflect on their own performance:

- `generation_source`
- `origin_agent`
- `pre_sim_confidence`
- `post_sim_verdict`
- `agent_latency_ms`
- `agent_cost_estimate`
- `research_artifact_version`
- `context_bundle_version`

### 3.2 Why this matters

Without these fields, the system cannot answer questions like:

- Did Hermes-generated alphas outperform template-generated alphas this week?
- Did DeerFlow-backed research improve pass rate or just increase latency?
- Were pre-simulation reviews calibrated, or were agents overconfident?
- Which research bundle version produced the best candidates?

That means the current system has:
- workflow memory,
- result persistence,
- and explainability,

but not true self-reflection or experiment-grade attribution.

### 3.3 Recommended backend additions

Minimum useful additions:

- `generation_source`
- `origin_agent`
- `pre_sim_confidence`
- `post_sim_verdict`
- `needs_review_reason`
- `failure_pattern_summary`

Recommended API additions:

- `GET /api/analytics/failure-patterns`
- `GET /api/analytics/generation-sources`
- `GET /api/analytics/review-calibration`
- `GET /api/analytics/theory-performance`

## 4. Research Pipeline Review

### 4.1 Current strength

The research pipeline does work.

Good parts:
- daily digest refresh exists,
- theory context exists,
- failure context exists,
- DeerFlow fallback routing is sensible,
- research artifacts are persisted.

### 4.2 Current weakness

Research is still too much of a black box from the operator perspective.

The system can produce research context, but it is harder to answer:

- Why was this run better than the previous run?
- Which artifact changed generation behavior?
- Did research improve pass rate or just produce more candidates?

This is not a correctness issue.
It is an observability issue.

## 5. Theory Explorer Review

### 5.1 Current status

Theory Explorer is functional but passive.

It can:
- read theory entries,
- filter them,
- add or update theory entries.

### 5.2 Missing exploration power

It does not yet behave like an actual research explorer because it lacks:

- strategy-aware theory filters,
- theory usage analytics,
- paper-to-alpha traceability,
- pass-rate by theory,
- theory heat map by generated count and quality.

### 5.3 Recommended next features

Minimum high-value additions:

- theory usage count,
- theory-linked alpha count,
- theory pass rate,
- theory warning rate,
- clickable trace from theory to matching alphas.

## 6. Benchmark Comparison

### 6.1 Alpha-GPT style Human-AI Interactive pattern

Reference gap:

- Hierarchical RAG:
  - Alpha Generator has knowledge-base RAG
  - status: partial match
- Thoughts decomposer:
  - Alpha Generator has explanation layer
  - status: good match
- Alpha IC tracking:
  - currently missing
- multi-round search enhancement:
  - currently missing as an explicit tracked loop
- seed-to-enhanced delta metric:
  - currently missing

Main implication:

The system does not yet track per-round improvement quality.
It can produce a result, but it cannot quantify which refinement round actually improved alpha quality the most.

### 6.2 Chain-of-Alpha style dual-chain architecture

Reference gap:

- Factor Generation Chain:
  - Alpha Generator has this
- Factor Optimization Chain:
  - still weak or missing as an automated loop
- Backtest feedback loop:
  - exists, but mostly manual in practice
- Prior knowledge memory:
  - exists through lessons learned memory
- No human intervention:
  - not a goal here, because Studio is intentionally human-in-the-loop

Main implication:

Alpha Generator currently behaves more like:
- generate,
- review,
- simulate,
- persist,

than:
- generate,
- optimize automatically from backtest feedback,
- re-run until quality converges.

### 6.3 W&B / MLflow style experiment tracking

Reference gap:

Missing or weak:
- per-step input/output tracking,
- latency tracing by agent step,
- token or cost tracing,
- run tags for commit/version/seed/context bundle,
- parameter sweep comparison UI.

Main implication:

The system is not yet experiment-grade reproducible.
Runs are inspectable, but not richly comparable.

### 6.4 WorldQuant-specific scoring and novelty tracking

Reference gap:

- Fitness is present, but still under-emphasized as a first-class operator-facing score
- portfolio-level correlation tracking is still missing
- operator does not yet get a strong novelty or additive-value view for a new alpha

Main implication:

The system can say whether an alpha passes a gate,
but not yet whether it adds real portfolio diversity value.

## 7. Priority Recommendations

### 7.1 Highest priority

1. Add SSE streaming for pipeline events and active-run UI.
2. Add Alpha Detail skeleton and explanation-pending state.
3. Add experiment tracking metadata for generation source and review confidence.

### 7.2 Second priority

1. Add theory analytics:
   - usage count
   - pass rate
   - linked alphas
2. Add structured failure pattern endpoints for agent self-reflection.
3. Add candidate lifecycle UX in Studio.

### 7.3 Third priority

1. Add optimization-chain loop from backtest result to auto-refinement.
2. Add per-step latency and cost tracing.
3. Add portfolio-level novelty and correlation analytics.

## 8. Bottom Line

The system is already credible as an automated alpha workbench.

Its current ceiling is limited less by architecture and more by missing observability loops.

What it already does well:
- generation,
- simulation,
- persistence,
- explainability,
- human review.

What it still needs to become truly strong:
- real-time operator feedback,
- experiment tracking,
- automatic quality trajectory measurement,
- research and theory analytics,
- deeper self-reflection signals for the agents themselves.
