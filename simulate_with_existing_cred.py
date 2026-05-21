"""Quick simulation script using existing project credentials + OpenRouter model.
This script generates 3 alphas via Hermes (with OpenRouter fallback) and simulates them
in dry-run mode so the user can evaluate the results quickly.
"""
from config import load_config
from pipeline.alpha_pipeline import AlphaPipeline
from pipeline.models import AlphaCandidate

def main():
    config = load_config()
    # Force dry-run for safety during this quick evaluation
    config.settings.setdefault("app", {})["dry_run"] = True
    config.env["WQ_DRY_RUN"] = "true"

    pipeline = AlphaPipeline(config)

    # Generate 3 alphas using the existing Hermes + OpenRouter fallback
    candidates = pipeline.llm_generator.generate("momentum", 3, "")
    print("=== Generated Alphas (via Hermes + OpenRouter) ===")
    for i, c in enumerate(candidates, 1):
        print(f"{i}. {c.expression}")

    print("\n=== Simulation Results (Dry-run) ===")
    for i, c in enumerate(candidates, 1):
        metrics = pipeline.simulator.run(c)
        print(f"{i}. {c.expression}")
        print(f"   Sharpe={metrics.sharpe:.3f} Fitness={metrics.fitness:.3f} Turnover={metrics.turnover:.3f}")
        print()

if __name__ == "__main__":
    main()
