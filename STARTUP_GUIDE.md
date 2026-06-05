# 🚀 Alpha Generator - Agent Startup Guide

## ⚠️ CRITICAL: Do This First!

When you start working on this project, **you MUST call the skill knowledge loader immediately:**

```
Call MCP Tool: get_skill_knowledge()
```

This loads the complete domain knowledge from `mcp_skill.md` which contains:
- ✅ Valid operators (ts_delta, ts_rank, group_rank, etc.)
- ❌ Broken operators to AVOID (ts_min, ts_max, delay, stddev)
- 📊 IQC Criteria: Sharpe ≥ 1.25, Fitness ≥ 1.0, Turnover 10-70%
- ⚙️ Advanced optimization techniques (Decay, Truncation, Neutralization rules)
- 📈 Proven settings grid for different alpha types
- 💡 Examples of high-quality composite alphas

**Why this matters:**
- Without this knowledge, you'll generate simple alphas that fail IQC
- You'll accidentally use broken operators
- You'll apply wrong neutralization (Market vs Subindustry)
- You'll miss critical turnover and drawdown optimization rules

---

## 📋 Recommended Startup Checklist

1. **Load Skill Knowledge** (MANDATORY)
   ```
   get_skill_knowledge()
   → Save entire output to your context!
   ```

2. **Read the Documentation**
   - `AGENTS_README.md` — System architecture (sections 1-4)
   - `MCP_USAGE.md` — Tool usage examples
   - `mcp_skill.md` — The knowledge base itself

3. **Understand the Workflow**
   - `search_knowledge_base()` first (find academic rationale)
   - `search_data_fields()` when exploring new variables
   - `submit_alpha()` to test (always dry_run=True initially)
   - `list_gold_alphas()` for inspiration
   - `mutate_from_gold()` to evolve formulas

4. **Start Your First Task**
   - Ask user what type of alpha they want
   - Search knowledge base for academic inspiration
   - Generate composite formula
   - Test with dry_run=True
   - Iterate based on metrics

---

## 🔄 Quick Reference: Workflow Loop

```
USER REQUEST
    ↓
get_skill_knowledge() [IF FIRST TIME]
    ↓
search_knowledge_base(query) [Find academic rationale]
    ↓
search_data_fields(query) [Discover new variables]
    ↓
Generate composite formula [Combine price+volume+fundamental+sentiment]
    ↓
submit_alpha(formula, dry_run=True) [Test first]
    ↓
Analyze metrics vs IQC criteria
    ↓
Iterate OR list_gold_alphas() for inspiration
```

---

## 🛑 Common Mistakes to Avoid

| ❌ WRONG | ✅ RIGHT |
|---------|----------|
| Generate basic alpha without knowledge | Call `get_skill_knowledge()` first |
| Use `ts_min`, `ts_max`, `delay` operators | Use `ts_arg_min`, `ts_arg_max`, `ts_delay` |
| Simple price formula: `rank(-ts_delta(close, 5))` | Composite: add volume, fundamental, sentiment signals |
| Apply Subindustry neutralization to price alphas | Use Market neutralization for price/volume alphas |
| Submit without checking IQC criteria | Verify: Sharpe ≥ 1.25, Fitness ≥ 1.0, Turnover 10-70% |
| Turnover > 50% | Apply `ts_decay_linear(signal, 5-10)` to reduce |

---

## 📚 Important Files

| File | Purpose |
|------|---------|
| `mcp_skill.md` | The single source of truth (loaded by `get_skill_knowledge()`) |
| `AGENTS_README.md` | System architecture and file map |
| `MCP_USAGE.md` | Tool usage guide with examples |
| `.kiro/steering/load-skill-on-startup.md` | Kiro framework guidance |
| `mcp_server.py` | MCP tool definitions |
| `wqb_automation.py` | WorldQuant Brain API client |
| `alpha_skills/knowledge_retriever.py` | Knowledge base search engine |

---

## 🎯 Success Criteria

You know you're doing it right when:
- ✅ You called `get_skill_knowledge()` first
- ✅ You search knowledge base before generating each formula
- ✅ Your alphas are composite (4+ signals blended)
- ✅ Your formulas use correct operators from skill knowledge
- ✅ You respect IQC thresholds (Sharpe ≥ 1.25, Fitness ≥ 1.0)
- ✅ You iterate based on metrics rather than guessing

---

Good luck! 🚀 Remember: **Load the skill knowledge first!**
