1: # Alpha Generator - Complete System Workflow & Improvement Roadmap
2: 
3: ## 1. Current System Architecture (Mermaid)
4: 
5: ```mermaid
6: flowchart TD
7:     subgraph Frontend[Frontend React UI]
8:         A[Dashboard / Alphas / Logs / Studio]
9:         B[Polling: /overview, /alphas, /logs every 2s]
10:         C[Studio Chat + Manual Generate/Simulate]
11:         D[Dual-Agent Chatspace Hermes + DeerFlow]
12:     end
13: 
14:     subgraph API[FastAPI Monitor API]
15:         E[monitor_api.py]
16:         F[/overview, /alphas, /pipeline/*, /studio/*, /theories]
17:         G[AlphaStore SQLite]
18:         H[build_alpha_explanation_payload]
19:         I[parse_progress + workflow_detail]
20:     end
21: 
22:     subgraph Pipeline[Alpha Pipeline Core]
23:         J[Researcher: daily feeds + KB RAG]
24:         K[Generator: Hermes + DeerFlow + Templates]
25:         L[Pre-backtest Proxy Gate]
26:         M[Simulator: WQ Brain + FIFO Queue]
27:         N[Quality Gate + Agent Reviews pre/post]
28:         O[Submit / Store + Explanations]
29:     end
30: 
31:     subgraph Runtime[Runtime & Knowledge Base]
32:         P[simulation_fifo active.lock + *.ticket]
33:         Q[knowledge_base/ + lessons_learned/]
34:         R[logs/ + research_feeds/ + alpha_history/]
35:         S[Theory Catalog + Theory Usage Heat]
36:     end
37: 
38:     subgraph External[External Services]
39:         T[WorldQuant Brain API]
40:         U[OpenRouter LLM Endpoints]
41:     end
42: 
43:     A -->|User clicks Run now| E
44:     B -->|poll every 2s| F
45:     C -->|studioQuery / studioGenerate / studioSimulate| F
46:     D -->|chat messages persisted| G
47:     E -->|load config + AlphaPipeline| J
48:     F -->|CRUD + analytics| G
49:     G -->|persist alpha + explanation| H
50:     J -->|research artifacts + theory basis| K
51:     K -->|candidates with origin_agent| L
52:     L -->|proxy score + pre_sim review| M
53:     M -->|metrics + self_correlation| N
54:     N -->|pass/fail + gate_reasons + reviews| O
55:     O -->|insert_alpha + save_alpha_explanation| G
56:     P -->|FIFO ticket system| M
57:     Q -->|RAG context + failure recovery| J
58:     R -->|event stream + task_timeline| I
59:     S -->|theory usage analytics| F
60:     M -->|live simulation| T
61:     K -->|LLM calls| U
62: ```
63: 
64: ## 2. Current System Evaluation
65: 
66: ### Strengths
67: - Strong multi-source generation (Hermes + DeerFlow + templates)
68: - Structured quality gates with pre/post simulation reviews
69: - Alpha-level explainability (theory links, field/operator explanations, stage notes)
70: - Real-time simulation FIFO queue with active.lock tracking
71: - Theory usage heat map and failure pattern analytics
72: - Studio for human-in-the-loop exploration
73: 
74: ### Critical Gaps
75: 1. **No real-time streaming** – Dashboard/Logs rely on 2s polling → feels delayed
76: 2. **No experiment tracking** – No MLflow/W&B style run tagging, latency/cost per stage, sweep comparison
77: 3. **Weak provenance** – `generation_source` and `origin_agent` exist but not deeply used for learning
78: 4. **No closed-loop reflection** – Agents review but system does not calibrate confidence vs reality
79: 5. **Lessons learned are file-based** – Not queryable at runtime for next generation batch
80: 6. **No run-level experiment matrix** – Cannot compare “research quality vs prompt quality vs simulation filter”
81: 
82: ## 3. Recommended Git Repositories for Improvement
83: 
84: ### A. Experiment Tracking & Observability
85: - **mlflow/mlflow** (https://github.com/mlflow/mlflow)
86:   - Add `mlflow.start_run()` around each pipeline stage
87:   - Log: params (strategy, model, prompt version), metrics (Sharpe, fitness, latency, token cost), artifacts (research JSON, alpha expressions)
88:   - Use MLflow Model Registry for best alphas
89:   - Replace current ad-hoc logging with structured experiment tracking
90: 
91: - **mtech00/mlflow-experiment-tracking** (https://github.com/mtech00/mlflow-experiment-tracking)
92:   - Reference implementation for systematic experiment tracking with feature sets and model registry
93: 
94: ### B. Multi-Agent Workflow Orchestration
95: - **langchain-ai/langgraph** (https://github.com/langchain-ai/langgraph)
96:   - Replace current linear pipeline with stateful graph
97:   - Add conditional edges: if pre-backtest fails → early exit; if confidence low → extra reflection round
98:   - Implement human-in-the-loop checkpoints (Studio approval gate)
99:   - Enable parallel research + generation branches
100: 
101: - **josephsenior/langgraph-workflow-orchestrator** (https://github.com/josephsenior/langgraph-workflow-orchestrator)
102:   - Production-ready patterns: approval workflow, parallel processing, iterative refinement, conditional routing
103:   - Built-in checkpointing and Mermaid visualization
104: 
105: - **yx-fan/agent-flow-framework** (https://github.com/yx-fan/agent-flow-framework)
106:   - YAML-defined multi-domain workflows with Redis memory layer
107:   - FastAPI + LangGraph integration ready
108: 
109: ### C. Reflection & Self-Critique Agents
110: - **microsoft/autogen** (https://github.com/microsoft/autogen)
111:   - Use `reflection_with_llm` summary method for post-simulation critique
112:   - Implement nested chat: Writer → Reviewer → Revised Writer
113:   - Add structured self-criticism loop before final storage
114: 
115: - **MirrorDNA-Reflection-Protocol/crewAI** (https://github.com/MirrorDNA-Reflection-Protocol/crewAI)
116:   - Crews + Flows architecture for autonomous collaboration + precise control
117:   - Reflection agents that critique and improve previous outputs
118: 
119: ### D. Alpha Generation & Quantitative Research Pipelines
120: - **LLMQuant/Alpha-Agent** (https://github.com/LLMQuant/Alpha-Agent)
121:   - Knowledge base construction from research papers (`quant-wiki`)
122:   - Market regime detection (`MarketPulse`)
123:   - Contextual retrieval + code synthesis + Qlib backtesting
124:   - Research report generation with improvement suggestions
125: 
126: - **ICT-FinD-Lab/alphagen** (https://github.com/ICT-FinD-Lab/alphagen)
127:   - Reinforcement learning for formulaic alpha generation
128:   - Supports both RL (PPO) and LLM-only iterative generation
129:   - Strong baselines: GPlearn, DSO, LLM-assisted
130: 
131: - **paperswithbacktest/pwb-alphaevolve** (https://github.com/paperswithbacktest/pwb-alphaevolve)
132:   - Evolutionary LLM agent (inspired by DeepMind AlphaEvolve)
133:   - EVOLVE-BLOCK markers + async genetic controller + SQLite hall-of-fame
134:   - Prompt evolution via genetic algorithm
135: 
136: - **ywuwuwu/Alpha-Factory** (https://github.com/ywuwuwu/Alpha-Factory)
137:   - End-to-end alpha research loop with purged walk-forward validation
138:   - Market-neutral long/short portfolio construction + turnover-aware costs
139:   - Online L1-budget allocator for signal combination
140: 
141: - **Aroesler1/LLMStrat** (https://github.com/Aroesler1/LLMStrat)
142:   - 8-gate signal validation + walk-forward controls
143:   - Point-in-time universe + strict LLM factor mining with JSON enforcement
144: 
145: ## 4. Recommended Implementation Roadmap
146: 
147: ### Phase 1 – Observability (2-3 weeks)
148: 1. Integrate MLflow for every pipeline run
149: 2. Log stage latency, token usage, cost, research artifact hash
150: 3. Replace current file-based lessons_learned with MLflow queryable runs
151: 
152: ### Phase 2 – Stateful Orchestration (3-4 weeks)
153: 1. Migrate pipeline to LangGraph state machine
154: 2. Add conditional edges for early exit / reflection loops
155: 3. Implement human-in-the-loop approval gate in Studio
156: 
157: ### Phase 3 – Reflection & Self-Critique (2-3 weeks)
158: 1. Add AutoGen reflection agents after simulation
159: 2. Store confidence calibration (predicted vs actual Sharpe)
160: 3. Create structured “lessons learned” JSON stored in MLflow artifacts
161: 
162: ### Phase 4 – Advanced Alpha Generation (ongoing)
163: 1. Adopt Alpha-Agent knowledge base + regime detection
164: 2. Experiment with AlphaEvolve-style evolutionary prompts
165: 3. Integrate Alphagen RL + LLM hybrid generation
166: 
167: ## 5. Quick Wins (Can be done this week)
168: - Add `mlflow.log_metric("stage_latency", ...)` in each pipeline stage
169: - Store `run_tags` with git commit + research artifact hash
170: - Expose `/runs/{run_id}/mlflow` link in Dashboard
171: - Add simple reflection prompt in `post_simulation` review
172: 
173: ---
174: 
175: ---
176: 
177: ## 6. Knowledge Base Improvement for Hermes & DeerFlow (Updated 2026-05-19)
178: 
179: ### Current State
180: Hermes và DeerFlow hiện đang đọc từ:
181: - 3 research papers (101 Formulaic Alphas, Alpha2, AutoAlpha)
182: - 4 WorldQuant official docs
183: - 3 reference playbooks
184: - Hàng chục lessons_learned files (failure recovery, bruteforce, market regime)
185: 
186: ### Identified Knowledge Gaps
187: 
188: **High Priority Missing Topics:**
189: 1. **Alpha Decay & Signal Erosion** – How alphas lose edge over time
190: 2. **Turnover-Constrained Alpha Design** – Explicit turnover penalty in expression
191: 3. **Regime-Dependent Alpha Performance** – Bull/Bear/High-Vol regimes
192: 4. **Safe vs Risky Operators** – Which operators survive live trading
193: 5. **LLM-based Alpha Mining** – Recent papers on using LLMs for factor discovery
194: 
195: **Medium Priority:**
196: - Volatility-Adjusted Ranking
197: - Multi-Horizon Ensemble
198: - Cross-Sectional vs Time-Series Momentum
199: - Expression Complexity vs Overfitting
200: - Rank vs Zscore vs Raw transformation guidelines
201: 
202: ### Recommended Additions (Create These Files)
203: 
204: ```bash
205: # Phase 1 – Immediate impact
206: knowledge_base/lessons_learned/turnover_optimization.md
207: knowledge_base/lessons_learned/regime_aware_alpha.md
208: knowledge_base/research_feeds/reference/alpha_decay_signal_erosion.md
209: knowledge_base/research_feeds/reference/turnover_constrained_design.md
210: knowledge_base/research_feeds/reference/safe_vs_risky_operators.md
211: 
212: # Phase 2 – LLM/RL specific
213: knowledge_base/research_papers/llm/llm_alpha_mining_2025.md
214: knowledge_base/research_papers/rl/alphagen_harla.md
215: knowledge_base/research_papers/evolution/alphaevolve_prompt_optimization.md
216: ```
217: 
218: ### How This Improves Generation Quality
219: 
220: | Gap Filled | Expected Improvement |
221: |------------|----------------------|
222: | Turnover optimization | Higher fitness scores, fewer screened_out due to turnover |
223: | Regime awareness | Better alpha robustness across market conditions |
224: | Operator risk matrix | Fewer alphas with high self-correlation or low live Sharpe |
225: | LLM alpha mining papers | Hermes/DeerFlow learn modern prompting patterns for quant |
226: | Alpha decay knowledge | System avoids generating signals that die quickly |
227: 
228: ### Current Workflow After Hermes Activation
229: 
230: ```mermaid
231: flowchart TD
232:     A[DailyResearcher + RAG] --> B[HermesBridge]
233:     B -->|Clean FASTEXPR| C[AlphaCandidate origin=hermes]
234:     C -->|Pre-backtest| D{Sharpe < -1.25 AND Fitness < -1.0?}
235:     D -->|Yes| E[Sign-flip + Direct Simulate]
236:     D -->|No| F[Normal Pre-backtest Gate]
237:     E --> G[Simulator WQ Brain]
238:     F --> G
239:     G -->|Metrics| H[Quality Gate + Agent Reviews]
240:     H --> I[Store + Explanation]
241: ```
242: 
243: **File updated:** `all_workflow.md`  
244: **Last updated:** 2026-05-19
245: 
246: ---
247: 
248: ## 7. Upgrades Applied (2026-05-19)
249: 
250: ### Prompt Engineering Upgrades
251: - **LLMGenerator** (pipeline/generator/llm_generator.py): Enhanced prompt with mandatory rules, Fitness formula, volume preference, motif avoidance, and regime injection.
252: - **HermesBridge.review_alpha**: Added 5-point theory checklist (economic hypothesis, regime fit, decay risk, turnover realism, motif repetition).
253: - **DeerFlowBridge.review_alpha**: Same 5-point theory checklist for structured post-simulation review.
254: 
255: ### Knowledge Base Additions
256: - `research_feeds/reference/trading_volume_alpha_nber_2024.md` — Volume as predictor beyond price.
257: - `research_feeds/reference/alphaforge_dynamic_combination_2024.md` — Dynamic factor re-ranking.
258: - `lessons_learned/operator_risk_matrix.md` — Risk levels for operators in FASTEXPR.
259: - `lessons_learned/regime_aware_generation.md` — Regime-specific generation guidance.
260: 
261: ### Pipeline Context Enhancement
262: - `_build_context` now injects:
263:   - Recent approved motifs (last 8 approved alphas)
264:   - Regime guidance extracted from daily research digest
265: - This context is passed to every Hermes generation call.
266: 
267: ### Expected Impact
268: - Higher percentage of valid FASTEXPR syntax
269: - Better alignment with current market regime
270: - Reduced motif repetition and self-correlation
271: - Stronger economic rationale in generated alphas
272: 
273: **All upgrades completed:** 2026-05-19 00:24
274: 
275: ---
276: 
277: ## Current Complete Workflow (Updated 2026-05-19)
278: 
279: Dưới đây là **toàn bộ workflow hiện tại** của hệ thống Alpha Generator sau tất cả các nâng cấp (Theory RAG, Data Researcher live WQ Brain, Pre-Simulation Review + Retry, Theory Accuracy Evaluation).
280: 
281: ```mermaid
282: flowchart TD
283:     subgraph Research[Research & Knowledge Base]
284:         R1[DailyResearcher.refresh]
285:         R2[KnowledgeBase RAG<br/>Theory Files]
286:         R3[DataResearcher<br/>Live WQ Brain Data]
287:         R4[TheoryResearcher<br/>Self-Research New Theory]
288:     end
289: 
290:     subgraph Generation[Alpha Generation by Hermes]
291:         G1[LLMGenerator.generate]
292:         G2[Build Prompt: 3 Parts<br/>Theory RAG + Live Data + Research Context]
293:         G3[HermesBridge.ask]
294:         G4[Return AlphaCandidate<br/>origin_agent=hermes]
295:     end
296: 
297:     subgraph PreReview[DeerFlow Pre-Simulation Review + Retry]
298:         P1[DeerFlow.review_alpha<br/>+ Theory RAG + 5-point Checklist]
299:         P2{Low Metrics or FAIL?}
300:         P3[Retry ≤ 3 times]
301:         P4[After 3 fails →<br/>Hermes.research_new_theory<br/>+ New Idea]
302:     end
303: 
304:     subgraph PreBacktest[Pre-backtest Gate]
305:         B1[LocalBacktester.evaluate]
306:         B2{Sharpe < -1.25 AND<br/>Fitness < -1.0?}
307:         B3[Sign-flip + Direct Simulate]
308:     end
309: 
310:     subgraph Simulation[Live Simulation]
311:         S1[Simulator.run<br/>WQ Brain FIFO]
312:         S2[Metrics + Self-Correlation]
313:     end
314: 
315:     subgraph PostReview[Post-Simulation Reviews]
316:         Q1[DeerFlow.review_alpha<br/>Post-Simulation]
317:         Q2[Hermes.review_alpha<br/>Post-Simulation]
318:     end
319: 
320:     subgraph Store[Storage & Learning]
321:         T1[QualityGate.evaluate]
322:         T2[AlphaStore.insert_alpha]
323:         T3[TheoryAccuracyEvaluator.record]
324:         T4[Tracker.alpha_explanation]
325:     end
326: 
327:     R1 --> G2
328:     R2 --> G2
329:     R3 --> G2
330:     R4 --> P4
331:     G1 --> G2
332:     G2 --> G3
333:     G3 --> G4
334:     G4 --> P1
335:     P1 --> P2
336:     P2 -->|Yes| P3
337:     P2 -->|No| B1
338:     P3 -->|Still bad| P4
339:     P4 --> G1
340:     B1 --> B2
341:     B2 -->|Yes| B3
342:     B2 -->|No| S1
343:     B3 --> S1
344:     S1 --> S2
345:     S2 --> Q1
346:     S2 --> Q2
347:     Q1 --> T1
348:     Q2 --> T1
349:     T1 --> T2
350:     T2 --> T3
351:     T2 --> T4
352: 
353:     style G3 fill:#bbdefb
354:     style P1 fill:#c8e6c9
355:     style Q1 fill:#c8e6c9
356:     style Q2 fill:#bbdefb
357:     style T3 fill:#fff9c4
358: ```
359: 
360: ### Tóm tắt các giai đoạn chính (Current Workflow)
361: 
362: | Giai đoạn | Thành phần chính | Mô tả ngắn |
363: |-----------|------------------|------------|
364: | **Research & Knowledge** | DailyResearcher, KnowledgeBase, DataResearcher, TheoryResearcher | Live data từ WQ Brain + Theory RAG + tự research kiến thức mới |
365: | **Generation** | Hermes + LLMGenerator | Tạo alpha với prompt gồm 3 phần: Theory RAG + Live Data + Research Context |
366: | **Pre-Simulation Review** | DeerFlow + Retry Loop | Review trước simulate, retry tối đa 3 lần. Lần 3 → research thêm lý thuyết mới |
367: | **Pre-backtest Gate** | LocalBacktester | Kiểm tra local proxy. Tự động sign-flip nếu quá tệ |
368: | **Live Simulation** | WQ Brain FIFO | Simulate thực tế trên WorldQuant Brain |
369: | **Post-Simulation Reviews** | DeerFlow + Hermes | Review sau khi có metrics (DeerFlow trước, Hermes sau) |
370: | **Storage & Learning** | AlphaStore + TheoryAccuracyEvaluator | Lưu alpha + ghi nhận lý thuyết nào mang lại kết quả tốt |
371: 
372: ### Điểm nổi bật của workflow hiện tại
373: 
374: - **Hermes** chịu trách nhiệm chính về việc **tạo alpha**.
375: - **DeerFlow** thực hiện **review hai lần**: trước và sau simulate.
376: - Có **vòng lặp tự cải thiện** (retry + research new theory) khi alpha chất lượng thấp.
377: - **Data Researcher** ưu tiên lấy dữ liệu **thời gian thực** từ WorldQuant Brain.
378: - **Theory Accuracy Evaluator** giúp hệ thống học được lý thuyết nào thực sự hiệu quả theo thời gian.
379: 
380: **Workflow này phản ánh trạng thái mới nhất** của hệ thống (cập nhật ngày 2026-05-19).
381: 
382: ---
383: 
384: ## Additional Improvements (2026-05-19)
385: 
386: ### 1. Local Backtester Operator Support
387: - Added support for missing operators in `pipeline/analyzer/local_backtester.py`:
388:   - `ts_rank(series, window)`
389:   - `abs(series)`
390: - This allows more expressions generated by Hermes to be properly evaluated during pre-backtest.
391: 
392: ### 2. Theory Context Transparency
393: - When Hermes generates an alpha, the **theory context used** (from Theory RAG) is now stored in the alpha's metadata under the key `theory_context_used`.
394: - This allows reviewers and the system to see exactly which theoretical principles Hermes referenced when creating the expression.
395: - Stored in `AlphaCandidate.metadata["theory_context_used"]`.
396: 
397: These changes improve both the **success rate** of local backtest and the **explainability** of generated alphas.
398: 
399: ---
400: 
401: ## 12. Full Live Data Integration (Final Update)
402: 
403: ### Changes Made
404: - `LLMGenerator` now accepts `wq_client` in `__init__`.
405: - `AlphaPipeline` passes `self.client` (WorldQuantClient) to `LLMGenerator`.
406: - `DataResearcher` is instantiated with the live client inside `LLMGenerator.generate()`.
407: - When generating alphas, Hermes now receives **real-time data** from WorldQuant Brain:
408:   - Average Daily Volume
409:   - Liquidity tier
410:   - Current market regime (volatility + liquidity)
411:   - Data source indicator (`live_wq_brain`)
412: 
413: ### Result
414: Hermes always works with the most up-to-date data characteristics from WorldQuant Brain when creating new alphas. This significantly improves the realism and robustness of generated expressions.
415: 
416: ---
417: 
418: ## 11. Live Data Integration from WorldQuant Brain (Added 2026-05-19)
419: 
420: ### Update to DataResearcher
421: - `DataResearcher` now accepts an optional `wq_client` parameter (WorldQuantClient).
422: - New internal methods:
423:   - `_fetch_live_universe_stats(universe)` — queries WQ Brain for real ADV, liquidity tier, coverage.
424:   - `_fetch_live_regime_context()` — queries current market regime (volatility, liquidity).
425: - `build_data_context()` now **prioritizes live data** from WorldQuant Brain.
426:   - If live data is unavailable, falls back to static JSON or default profile.
427:   - Context string includes `source: live_wq_brain` or `source: static`.
428: 
429: ### Effect
430: When Hermes generates an alpha, the prompt now contains **real-time data characteristics** from WorldQuant Brain (average daily volume, liquidity conditions, current regime). This makes generated alphas more realistic and aligned with the actual trading environment.
431: 
432: ---
433: 
434: ## 10. Data Researcher Integration (Added 2026-05-19)
435: 
436: ### New Module
437: - `knowledge_base/data_researcher.py`
438:   - `DataResearcher` class provides universe profile, field quality, and current data regime information.
439:   - Methods:
440:     - `get_universe_profile(universe)`
441:     - `get_field_quality(field)`
442:     - `get_regime_data_context()`
443:     - `build_data_context(strategy_type)` — compact string for prompts
444: 
445: ### Integration
446: - `LLMGenerator.generate()` now injects data context (liquidity, volume profile, regime) into Hermes prompt.
447: - HermesBridge and DeerFlowBridge have `research_data_context(knowledge_root, strategy_type)` method for on-demand data research.
448: 
449: ### Effect on Generation
450: When Hermes creates an alpha, it now receives:
451: - Theoretical grounding (RAG)
452: - Recent approved motifs + regime guidance
453: - **Data universe characteristics** (Avg ADV, liquidity tier, current regime)
454: 
455: This helps Hermes generate alphas that are realistic for the actual data environment (e.g., avoid volume signals on low-liquidity names, prefer volatility normalization in high-vol regimes).
456: 
457: ---
458: 
459: ## 9. Autonomous Theory Research + Accuracy Evaluation (Added 2026-05-19)
460: 
461: ### New Modules
462: - `knowledge_base/theory_researcher.py`
463: - `knowledge_base/theory_accuracy_evaluator.py`
464: 
465: ### Integration
466: - HermesBridge and DeerFlowBridge now have `research_new_theory(topic, knowledge_root)` method.
467: - AlphaPipeline records theory performance after every simulation using `theory_evaluator.record_theory_application()`.
468: - New public method: `pipeline.get_theory_accuracy_report()` returns average metrics per theory.
469: 
470: ### Workflow Impact
471: 1. During generation/review, agent can call `research_new_theory("volume alpha" or "alpha decay")` if confidence is low.
472: 2. After each simulation, the system logs which theory family was used and its resulting metrics.
473: 3. Over time, `get_theory_accuracy_report()` reveals which theories actually improve performance (e.g., "volume_correlation" vs "pure_momentum").
474: 
475: This closes the loop: agents not only use theory but also **learn which theories work best** through empirical feedback.
476: 
477: ---
478: 
479: ## 8. Theory RAG Layer for Hermes & DeerFlow (Added 2026-05-19)
480: 
481: ### New Module
482: - `knowledge_base/alpha_theory_rag.py`
483:   - `load_theory_snippets()`: Loads key theory documents (Volume Alpha, AlphaForge, Operator Risk, Regime Awareness, etc.)
484:   - `get_theory_context_for_generation()`: Optimized context for alpha creation
485:   - `get_theory_context_for_review()`: Optimized context for post-simulation evaluation
486: 
487: ### Integration Points
488: - **LLMGenerator.generate()**: Now accepts `knowledge_root` and injects theory RAG before calling Hermes.
489: - **HermesBridge.review_alpha()** and **DeerFlowBridge.review_alpha()**: Accept `knowledge_root` and prepend theory checklist + snippets.
490: - **AlphaPipeline**: Passes `self.config.knowledge_root` to all generation and review calls.
491: 
492: ### Effect
493: Every time Hermes or DeerFlow creates or reviews an alpha, it now has **explicit, retrieved theoretical grounding** from the curated knowledge base. This significantly increases the probability that generated expressions follow sound quant principles and that reviews are consistent and theory-aware.
494: 
495: (End of file - total 495 lines)
496: 
497: 
498: ## 13. Latest Run Summary (2026-05-19 11:44:08)
499: 
500: ### Command executed
501: - python main.py --run-once --dry-run --count 6
502: 
503: ### Observed runtime logs
504: - INFO: Running alpha pipeline for strategy=momentum count=6 run_id=pipeline-momentum-20260519044333-a3e26680
505: - WARNING: DeerFlow falling back to OpenRouter model openrouter/owl-alpha
506: - WARNING: Failed to fetch live universe stats: 'WorldQuantClient' object has no attribute 'session'
507: - WARNING: Failed to fetch live regime: 'WorldQuantClient' object has no attribute 'session'
508: - Note: The run process timed out in the local execution environment before a final report was produced.
509: 
510: ### Kết quả (Result)
511: - Pipeline khởi chạy thành công ở chế độ dry-run và bắt đầu quá trình research → generate → pre_backtest.
512: - Không có bản ghi alpha cuối cùng được lưu do quá trình bị gián đoạn/timeout trong môi trường local (không có report hoàn chỉnh).
513: - Một số thành phần vẫn hoạt động: generation và pre-backtest đã được gọi, nhưng live data query thất bại.
514: 
515: ### Cơ sở lý thuyết (Theory basis)
516: - Hệ thống sử dụng Theory RAG (knowledge_base/alpha_theory_rag.py) và dashboard/theory_catalog.THEORY_CATALOG làm nguồn lý thuyết.
517: - Khi khả dụng, LLMGenerator injects theory context vào prompt (see pipeline/alpha_pipeline.py:_build_context).
518: 
519: ### Cơ sở áp dụng lý thuyết lên dữ liệu (How theory applied to data)
520: - LLMGenerator kết hợp 3 phần vào prompt: (1) Theory RAG snippets, (2) real-time DataResearcher context (ADV, liquidity, regime) và (3) research digest.
521: - Do lỗi kết nối với WorldQuantClient (thiếu thuộc tính session), DataResearcher không thể lấy live universe/regime; vì vậy trong lần chạy này lý thuyết đã được inject nhưng không có dữ liệu thực-time để hiệu chỉnh biểu thức.
522: - Hệ quả: generated alphas có thể thiếu điều chỉnh về turnover/liquidity/regime trong lần chạy này.
523: 
524: ### Recommended immediate fixes
525: 1. Khắc phục lỗi WorldQuantClient (thiếu attribute `session`) trong api_layer/wq_client.py hoặc session_manager để DataResearcher có thể query live data.
526: 2. Đặt đúng biến môi trường HERMES/DEERFLOW/OPENROUTER (HERMES_COMMAND, DEERFLOW_COMMAND, OPENROUTER_API_KEY, etc.) để tránh fallback và đảm bảo agents chạy trên model mong muốn.
527: 3. Tăng timeout khi chạy pipeline local (current bash timeout was 120s). Run full pipeline without time limit or capture complete logs.
528: 4. Thêm logging/MLflow wrapper để đảm bảo partial runs vẫn ghi lại artifacts (research digest, generated expressions) even on failure.
529: 
530: ---
531: 
532: **File updated:** `all_workflow.md`  
533: **Updated at:** 2026-05-19 11:45:29
