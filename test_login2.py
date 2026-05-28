from wqb_automation import WQBAutomation, load_config

print("=== Login Test ===", flush=True)
config = load_config()
config['headless'] = False
config['timeout_ms'] = 60000

auto = WQBAutomation(config)
auto.start()

logged_in = auto.login()
print(f"Logged in: {logged_in}", flush=True)

if logged_in:
    print("Navigating to simulate...", flush=True)

auto.stop()
print("Done", flush=True)
