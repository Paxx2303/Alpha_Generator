# Alpha Generator - Complete System Workflow & Improvement Roadmap

## 1. Current System Architecture (Mermaid)

```mermaid
flowchart TD
    subgraph Frontend[Frontend React UI]
        A[Dashboard / Alphas / Logs / Studio]
        B[Polling: /overview, /alphas, /logs every 2s]
        C[Studio Chat + Manual Generate/Simulate]
        D[Dual-Agent Chatspace Hermes + DeerFlow]
    end

    subgraph API[FastAPI Monitor API]
        E[monitor_api.py]
        F[/overview, /alphas, /pipeline/*, /studio/*, /theories]
        G[AlphaStore SQLite]
        H[build_alpha_explanation_payload]
        I[parse_progress + workflow_detail]
    end

    subgraph Pipeline[Alpha Pipeline Core]
        J[Researcher: daily feeds + KB RAG]
        K[Generator: Hermes + DeerFlow + Templates]
        L[Pre-backtest Proxy Gate]
        M[Simulator: WQ Brain + FIFO Queue]
        N[Quality Gate + Agent Reviews pre/post]
        O[Submit / Store + Explanations]
    end

    subgraph Runtime[Runtime & Knowledge Base]
        P[simulation_fifo active.lock + *.ticket]
        Q[knowledge_base/ + lessons_learned/]
        R[logs/ + research_feeds/ + alpha_history/]
        S[Theory Catalog + Theory Usage Heat]
    end

    subgraph External[External Services]
        T[WorldQuant Brain API]
        U[OpenRouter LLM Endpoints]
    end

    A -->|User clicks Run now| E
    B -->|poll every 2s| F
    C -->|studioQuery / studioGenerate / studioSimulate| F
    D -->|chat messages persisted| G
    E -->|load config + AlphaPipeline| J
    F -->|CRUD + analytics| G
    G -->|persist alpha + explanation| H
    J -->|research artifacts + theory basis| K
    K -->|candidates with origin_agent| L
    L -->|proxy score + pre_sim review| M
    M -->|metrics + self_correlation| N
    N -->|pass/fail + gate_reasons + reviews| O
    O -->|insert_alpha + save_alpha_explanation| G
    P -->|FIFO ticket system| M
    Q -->|RAG context + failure recovery| J
    R -->|event stream + task_timeline| I
    S -->|theory usage analytics| F
    M -->|live simulation| T
    K -->|LLM calls| U
```

## 2. Current System Evaluation

### Strengths
- Strong multi-source generation (Hermes + DeerFlow + templates)
- Structured quality gates with pre/post simulation reviews
- Alpha-level explainability (theory links, field/operator explanations, stage notes)
- Real-time simulation FIFO queue with active.lock tracking
- Theory usage heat map and failure pattern analytics
- Studio for human-in-the-loop exploration

### Critical Gaps
1. **No real-time streaming** – Dashboard/Logs rely on 2s polling → feels delayed
2. **No experiment tracking** – No MLflow/W&B style run tagging, latency/cost per stage, sweep comparison
3. **Weak provenance** – `generation_source` and `origin_agent` exist but not deeply used for learning
4. **No closed-loop reflection** – Agents review but system does not calibrate confidence vs reality
5. **Lessons learned are file-based** – Not queryable at runtime for next generation batch
6. **No run-level experiment matrix** – Cannot compare “research quality vs prompt quality vs simulation filter”

## 3. Recommended Git Repositories for Improvement

### A. Experiment Tracking & Observability
- **mlflow/mlflow** (https://github.com/mlflow/mlflow)
  - Add `mlflow.start_run()` around each pipeline stage
  - Log: params (strategy, model, prompt version), metrics (Sharpe, fitness, latency, token cost), artifacts (research JSON, alpha expressions)
  - Use MLflow Model Registry for best alphas
  - Replace current ad-hoc logging with structured experiment tracking

- **mtech00/mlflow-experiment-tracking** (https://github.com/mtech00/mlflow-experiment-tracking)
  - Reference implementation for systematic experiment tracking with feature sets and model registry

### B. Multi-Agent Workflow Orchestration
- **langchain-ai/langgraph** (https://github.com/langchain-ai/langgraph)
  - Replace current linear pipeline with stateful graph
  - Add conditional edges: if pre-backtest fails → early exit; if confidence low → extra reflection round
  - Implement human-in-the-loop checkpoints (Studio approval gate)
  - Enable parallel research + generation branches

- **josephsenior/langgraph-workflow-orchestrator** (https://github.com/josephsenior/langgraph-workflow-orchestrator)
  - Production-ready patterns: approval workflow, parallel processing, iterative refinement, conditional routing
  - Built-in checkpointing and Mermaid visualization

- **yx-fan/agent-flow-framework** (https://github.com/yx-fan/agent-flow-framework)
  - YAML-defined multi-domain workflows with Redis memory layer
  - FastAPI + LangGraph integration ready

### C. Reflection & Self-Critique Agents
- **microsoft/autogen** (https://github.com/microsoft/autogen)
  - Use `reflection_with_llm` summary method for post-simulation critique
  - Implement nested chat: Writer → Reviewer → Revised Writer
  - Add structured self-criticism loop before final storage

- **MirrorDNA-Reflection-Protocol/crewAI** (https://github.com/MirrorDNA-Reflection-Protocol/crewAI)
  - Crews + Flows architecture for autonomous collaboration + precise control
  - Reflection agents that critique and improve previous outputs

### D. Alpha Generation & Quantitative Research Pipelines
- **LLMQuant/Alpha-Agent** (https://github.com/LLMQuant/Alpha-Agent)
  - Knowledge base construction from research papers (`quant-wiki`)
  - Market regime detection (`MarketPulse`)
  - Contextual retrieval + code synthesis + Qlib backtesting
  - Research report generation with improvement suggestions

- **ICT-FinD-Lab/alphagen** (https://github.com/ICT-FinD-Lab/alphagen)
  - Reinforcement learning for formulaic alpha generation
  - Supports both RL (PPO) and LLM-only iterative generation
  - Strong baselines: GPlearn, DSO, LLM-assisted

- **paperswithbacktest/pwb-alphaevolve** (https://github.com/paperswithbacktest/pwb-alphaevolve)
  - Evolutionary LLM agent (inspired by DeepMind AlphaEvolve)
  - EVOLVE-BLOCK markers + async genetic controller + SQLite hall-of-fame
  - Prompt evolution via genetic algorithm

- **ywuwuwu/Alpha-Factory** (https://github.com/ywuwuwu/Alpha-Factory)
  - End-to-end alpha research loop with purged walk-forward validation
  - Market-neutral long/short portfolio construction + turnover-aware costs
  - Online L1-budget allocator for signal combination

- **Aroesler1/LLMStrat** (https://github.com/Aroesler1/LLMStrat)
  - 8-gate signal validation + walk-forward controls
  - Point-in-time universe + strict LLM factor mining with JSON enforcement

## 4. Recommended Implementation Roadmap

### Phase 1 – Observability (2-3 weeks)
1. Integrate MLflow for every pipeline run
2. Log stage latency, token usage, cost, research artifact hash
3. Replace current file-based lessons_learned with MLflow queryable runs

### Phase 2 – Stateful Orchestration (3-4 weeks)
1. Migrate pipeline to LangGraph state machine
2. Add conditional edges for early exit / reflection loops
3. Implement human-in-the-loop approval gate in Studio

### Phase 3 – Reflection & Self-Critique (2-3 weeks)
1. Add AutoGen reflection agents after simulation
2. Store confidence calibration (predicted vs actual Sharpe)
3. Create structured “lessons learned” JSON stored in MLflow artifacts

### Phase 4 – Advanced Alpha Generation (ongoing)
1. Adopt Alpha-Agent knowledge base + regime detection
2. Experiment with AlphaEvolve-style evolutionary prompts
3. Integrate Alphagen RL + LLM hybrid generation

## 5. Quick Wins (Can be done this week)
- Add `mlflow.log_metric("stage_latency", ...)` in each pipeline stage
- Store `run_tags` with git commit + research artifact hash
- Expose `/runs/{run_id}/mlflow` link in Dashboard
- Add simple reflection prompt in `post_simulation` review

---

**File generated:** `all_workflow.md`  
**Last updated:** 2026-05-18
