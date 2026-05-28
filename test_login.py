import sys
sys.path.insert(0, '.')
from wqb_automation import WQBAutomation, load_config

log_file = open('wqb_logs/test_output.log', 'w', encoding='utf-8')
sys.stdout = log_file
sys.stderr = log_file

print('=== Full Alpha Submission Test ===')
config = load_config()
config['headless'] = True
config['timeout_ms'] = 60000

auto = WQBAutomation(config)
auto.start()

logged_in = auto.login()
print(f'Logged in: {logged_in}')

if logged_in:
    result = auto.submit_alpha("-rank(ts_delta(close, 5))")
    print(f'\n=== RESULT ===')
    for k, v in result.items():
        print(f'  {k}: {v}')

auto.stop()
log_file.close()
