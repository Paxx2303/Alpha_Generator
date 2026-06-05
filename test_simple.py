from wqb_automation import WQBAutomation, load_config
import json

config = load_config()
auto = WQBAutomation(config)
auto.start()
auto.login()

# Test simple baseline alpha
formula = 'rank(-ts_delta(close, 5))'
settings = 'TOP3000|Market|0|0.05'
print('Testing SIMPLE mean reversion baseline...')
result = auto.submit_alpha(formula, settings)
print('SIMPLE ALPHA RESULT:')
print(f'Sharpe: {result.get("sharpe", "N/A")}')
print(f'Fitness: {result.get("fitness", "N/A")}') 
print(f'Turnover: {result.get("turnover", "N/A")}')
print(json.dumps({k: v for k, v in result.items() if k != 'raw_api_response'}, indent=2))
auto.stop()