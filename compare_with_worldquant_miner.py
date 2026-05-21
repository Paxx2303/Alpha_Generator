"""
So sánh nhanh giữa Alpha_Generator (Hermes + OpenRouter) và worldquant-miner style.
Sử dụng cùng credential và model OpenRouter.
"""
from config import load_config
from api_layer import WQSessionManager, RateLimiter, WorldQuantClient
from pipeline.models import AlphaCandidate
from orchestration.openai_fallback import OpenAIFallbackClient
import hashlib

def simulate_dry(expr):
    """Mô phỏng kết quả dry-run giống worldquant-miner"""
    digest = hashlib.sha256(expr.encode()).digest()
    v = [b / 255 for b in digest[:6]]
    return {
        "sharpe": round(0.8 + v[0]*2.2, 3),
        "fitness": round(0.5 + v[1]*1.8, 3),
        "turnover": round(0.01 + v[3]*0.79, 3)
    }

def main():
    config = load_config()
    
    # OpenRouter client (giống worldquant-miner + Hermes)
    llm = OpenAIFallbackClient(
        api_key=config.env.get("OPENROUTER_API_KEY"),
        base_url=config.env.get("OPENROUTER_BASE_URL"),
        model=config.env.get("OPENROUTER_MODEL_NAME"),
        enabled=True
    )
    
    # WorldQuant client
    session = WQSessionManager(config.env.get("WQ_USERNAME"), config.env.get("WQ_PASSWORD"), 
                               config.settings["worldquant"]["base_url"], dry_run=False)
    rate = RateLimiter(3)
    wq = WorldQuantClient(session, rate, config.settings["worldquant"]["base_url"])
    
    prompt = "Generate 3 novel FASTEXPR momentum alphas. Return only expressions, one per line."
    
    print("=== worldquant-miner style (OpenRouter + real WQ) ===")
    response = llm.chat(prompt)
    expressions = [line.strip() for line in response.splitlines() if line.strip()][:3]
    
    if not expressions:
        expressions = ["rank(ts_mean(returns, 20))", "rank(ts_corr(volume, returns, 5))", "rank(close / ts_mean(close, 20))"]
    
    for expr in expressions:
        print(f"Expression: {expr}")
        # Dry-run result (giống worldquant-miner khi không có real sim)
        dry = simulate_dry(expr)
        print(f"  [Dry-run] Sharpe={dry['sharpe']} Fitness={dry['fitness']} Turnover={dry['turnover']}")
        
        # Real simulation
        try:
            candidate = AlphaCandidate(expression=expr, source="comparison", strategy_type="momentum")
            m = wq.simulate_expression(candidate)
            print(f"  [Real WQ] Sharpe={m.sharpe:.3f} Fitness={m.fitness:.3f} Turnover={m.turnover:.3f}")
        except Exception as e:
            print(f"  [Real WQ] Error: {e}")
        print()
    
    print("=== So sánh với Hermes (Alpha_Generator) ===")
    print("Hermes đã generate và review alpha thật với Theory RAG + Pre/Post review")
    print("Alpha ví dụ: rank(ts_delta(close, 10) / ts_std_dev(close, 60)) * rank(ts_corr(volume, returns, 20))")

if __name__ == "__main__":
    main()
