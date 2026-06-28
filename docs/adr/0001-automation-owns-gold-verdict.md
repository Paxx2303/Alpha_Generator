# Automation layer is the single source of truth for the gold verdict

The WQB automation layer (`wqb_automation.submit_alpha`) is the only place that decides whether a candidate is a gold alpha. It runs the full Submission Check — IS hard checks (`check_all_is_checks`) plus Self-Correlation (`check_self_correlation`) — and encodes the verdict in `metrics["status"]`, writing the `gold_alphas` / `failed_alphas` tables itself. Downstream callers (the MCP tool DeerFlow uses, the dashboard) must **read** that verdict and never recompute it.

## Context

Two submit paths had drifted apart. `wqb_automation.submit_alpha` ran the full check and set `status` (UNSUBMITTED / CORRELATED / FAIL_CHECKS). But `core/mcp/tools/alpha.py` — the path DeerFlow actually calls — then ran its *own* `_is_gold()` that checked only Sharpe/Fitness/Turnover and re-saved gold via `upsert_gold_alpha`. Alphas the automation had rejected as Correlated or Check-Failed were re-promoted to gold, polluting the gold table with alphas WQB would reject at submit time.

## Decision

Delete the duplicate verdict logic from the MCP tool. It keeps `save_alpha_result` (it is the sole writer of the `alpha_results` log) but trusts `metrics["status"]` for the gold/failed decision and surfaces `status` + `self_correlation` back to DeerFlow so the agent can see *why* an alpha was rejected.

## Considered options

- **MCP tool re-validates with matching criteria** — rejected: two copies of the criteria will drift again; the bug was exactly this drift.
- **Interactive "Check Submission" button in the dashboard** — rejected: the dashboard is read-only, public, and has no WQB credentials; a live-checking button would force a `:rw` mount, credential injection, and an auth gate. The check is made automatic instead.

## Consequences

- PENDING self-correlation is treated optimistically (counts as gold now) and resolved later by running `check_self_corr.py`. The gold table can briefly hold an unverified alpha; this is an accepted trade-off for keeping the path simple and button-free.
