import sys; sys.stdout.reconfigure(line_buffering=True)
from wqb_automation import WQBAutomation, load_config

print("=== Headless Login Test ===", flush=True)
config = load_config()
config['headless'] = True
config['timeout_ms'] = 60000

auto = WQBAutomation(config)
auto.start()

logged_in = auto.login()
print(f"Logged in: {logged_in}", flush=True)

if logged_in:
    result = auto.submit_alpha("-rank(ts_delta(close, 5))")
    print(f"\n=== RESULT ===", flush=True)
    for k, v in result.items():
        print(f"  {k}: {v}", flush=True)

auto.stop()
print("Done", flush=True)
