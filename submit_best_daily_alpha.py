import json
import logging
from pathlib import Path
from wqb_automation import WQBAutomation, load_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GOLD_ALPHAS_PATH = Path(__file__).parent / "gold_alphas.json"

def main():
    if not GOLD_ALPHAS_PATH.exists():
        logger.info("No gold_alphas.json found.")
        return

    with open(GOLD_ALPHAS_PATH, 'r', encoding='utf-8') as f:
        alphas = json.load(f)

    unsubmitted = [a for a in alphas if a.get("status") == "UNSUBMITTED"]
    if not unsubmitted:
        logger.info("No unsubmitted alphas found today. Good job!")
        return

    # Calculate Quality Score = Sharpe * Fitness
    def get_score(alpha):
        return alpha.get("sharpe", 0) * alpha.get("fitness", 0)

    # Sort descending
    unsubmitted.sort(key=get_score, reverse=True)
    best_alpha = unsubmitted[0]
    
    logger.info(f"Selected best alpha: {best_alpha.get('name')} (ID: {best_alpha.get('id')})")
    logger.info(f"Score: {get_score(best_alpha):.4f} (Sharpe: {best_alpha.get('sharpe')}, Fitness: {best_alpha.get('fitness')})")
    
    config = load_config()
    auto = WQBAutomation(config)
    auto.start()
    
    if auto.login():
        logger.info("Submitting the best alpha to the exchange...")
        res = auto.submit_saved_alpha(best_alpha["id"])
        
        if res.get("status") == "SUCCESS":
            logger.info("Submission SUCCESS!")
            # Update status in json
            for a in alphas:
                if a.get("id") == best_alpha["id"]:
                    a["status"] = "SUBMITTED_SUCCESS"
            
            with open(GOLD_ALPHAS_PATH, 'w', encoding='utf-8') as f:
                json.dump(alphas, f, indent=2, ensure_ascii=False)
        else:
            logger.error(f"Submission FAILED: {res}")
            
    auto.stop()

if __name__ == "__main__":
    main()
