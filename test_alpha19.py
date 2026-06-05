from wqb_automation import WQBAutomation, load_config
import json

config = load_config()
auto = WQBAutomation(config)
auto.start()
auto.login()

# Alpha 19: Kyle's Lambda - Informed Trading Signal
formula = """
price_impact = abs(returns) / (volume / adv20 + 0.001);
kyle_lambda = ts_mean(price_impact, 20);
informed_signal = rank(kyle_lambda);
order_imbalance = (close - open) / (open + 0.0001);
volume_trend = rank(ts_delta(volume, 5));
composite = 0.5 * informed_signal + 0.3 * rank(order_imbalance) + 0.2 * volume_trend;
rank(ts_decay_linear(composite, 6))
""".strip()

settings = 'TOP3000|Market|5|0.06'
print('Submitting Alpha 19: Kyles Lambda Informed Trading...')
result = auto.submit_alpha(formula, settings)
print(json.dumps({k: v for k, v in result.items() if k != 'raw_api_response'}, indent=2))

sharpe = result.get('sharpe', 0)
fitness = result.get('fitness', 0)
if sharpe >= 1.25 and fitness >= 1.0:
    print('\n🎉 GOLD ALPHA!')
elif sharpe >= 1.25:
    print(f'\n✅ Good Sharpe={sharpe:.2f}! Fitness={fitness:.2f}')
else:
    print(f'\n⚠️ Sharpe={sharpe:.2f}, Fitness={fitness:.2f}')
    
auto.stop()
