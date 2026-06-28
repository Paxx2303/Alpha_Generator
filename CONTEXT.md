# Alpha Generator

An autonomous AI researcher that discovers and verifies alpha signals on WorldQuant Brain (WQB). This glossary pins the vocabulary used across the Core / Operation / Observation layers.

## Language

**Alpha**:
A formula (WQB FASTEXPR expression) that produces a trading signal, together with the market setting it was simulated under.
_Avoid_: signal (reserve for the raw pre-transform expression), strategy.

**Gold alpha**:
An alpha that has passed *every* automatic check and is therefore submittable to the WQB exchange. Being "gold" is the verdict of the Submission Check — not merely meeting the IS criteria.
_Avoid_: good alpha, winner, passing alpha.

**IS criteria**:
The in-sample numeric gates a candidate must clear: Sharpe ≥ 1.25, Fitness ≥ 1.0, Turnover 10–70%. Necessary but not sufficient for gold.
_Avoid_: thresholds, pass criteria.

**Submission Check**:
The full automatic verdict pipeline that decides whether a candidate is a gold alpha: the IS hard checks plus the Self-Correlation check, run against the live WQB alpha record. The single source of truth for the gold verdict.
_Avoid_: automation check, validation, IQC (IQC is WQB's UI name, not ours).

**Self-Correlation**:
How similar a candidate alpha is to alphas already submitted. A value ≥ 0.7 blocks submission; such an alpha is rejected as Correlated even if it meets the IS criteria.
_Avoid_: similarity, overlap.

**Verdict (status)**:
The outcome the Submission Check assigns to a candidate. Canonical outcomes: *Submittable* (gold, awaiting exchange submit), *Correlated* (self-corr ≥ 0.7), *Check-Failed* (a hard IS check failed). The verdict is owned by the automation layer, never recomputed downstream.
_Avoid_: result, grade.

**Market setting**:
The simulation configuration a research session runs under, written `UNIVERSE|NEUTRALIZATION|DECAY|TRUNCATION` (e.g. `TOP1000|INDUSTRY|3|0.08`). The research daemon rotates through a fixed list of these.
_Avoid_: config, parameters, environment.

**Research session**:
One bounded run of the empirical loop under a single market setting, ending when a gold alpha is found or the rotation timeout elapses.
_Avoid_: cycle (ambiguous with cron tick), run.

**Source effectiveness**:
The rate at which a knowledge source yields gold alphas, used to prioritise which sources DeerFlow draws from. Computed with Bayesian smoothing so low-sample sources aren't over-trusted.
_Avoid_: source score, quality.
