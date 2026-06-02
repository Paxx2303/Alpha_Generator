import sys
sys.stdout.reconfigure(encoding='utf-8')
from wqb_automation import WQBAutomation, load_config
import time
import json

def auto_optimize():
    config = load_config()
    auto = WQBAutomation(config)
    auto.start()
    
    if not auto.login():
        print("Login failed")
        return
        
    # Các kịch bản thử nghiệm: Đảo dấu công thức và tăng Decay / Đổi Neutralization để ép Fitness lên 1.0+
    # Kịch bản tối ưu hóa Turnover và Returns
    formulas_to_test = [
        # Thử nghiệm 1: Linear Decay kết hợp Subindustry và Truncation 0.01
        ("signal = -rank(ts_decay_linear(ts_delta(close, 5), 5)); signal", "TOP3000|Subindustry|0|0.01"),
        ("signal = -rank(ts_decay_linear(ts_delta(close, 5), 5)); signal", "TOP3000|Subindustry|3|0.01"),
        
        # Thử nghiệm 2: Lazy Updating (Trade_when returns > 0.02)
        ("raw_signal = -rank(ts_delta(close, 5)); condition = abs(returns) > 0.02; trade_when(condition, raw_signal, ts_delay(raw_signal, 1))", "TOP3000|Subindustry|0|0.01"),
        ("raw_signal = -rank(ts_delta(close, 5)); condition = abs(returns) > 0.02; trade_when(condition, raw_signal, ts_delay(raw_signal, 1))", "TOP3000|Market|3|0.01"),
        
        # Thử nghiệm 3: Signal Blending (Trộn Price & Volume)
        ("signal = -rank(ts_delta(close, 5)) - rank(ts_delta(volume, 5)); signal", "TOP3000|Subindustry|0|0.01"),
        ("signal = -rank(ts_delta(close, 5)) - rank(ts_delta(volume, 5)); signal", "TOP3000|Subindustry|5|0.01"),
        
        # Thử nghiệm 4: All-in-One (Blending + Linear Decay + Truncation 0.01 + Subindustry)
        ("signal = -rank(ts_decay_linear(ts_delta(close, 5), 5)) - rank(ts_decay_linear(ts_delta(volume, 5), 5)); signal", "TOP3000|Subindustry|3|0.01"),
    ]
    
    print("========================================")
    print(" BẮT ĐẦU VÒNG LẶP TÌM KIẾM ALPHA CHUẨN")
    print("========================================")
    
    passed = False
    
    for formula, settings in formulas_to_test:
        print(f"\n[TEST] Formula: {formula}")
        print(f"       Settings: {settings}")
        res = auto.submit_alpha(formula, settings)
        
        if "error" in res:
            print(f"Lỗi: {res['error']}")
            continue
            
        sharpe = float(res.get("sharpe", 0))
        fitness = float(res.get("fitness", 0))
        turnover = float(res.get("turnover", 0))
        
        print(f">>> KẾT QUẢ: Sharpe: {sharpe:.2f} | Fitness: {fitness:.2f} | Turnover: {turnover:.4f}")
        
        # Tiêu chí IQC PASS cơ bản
        if sharpe >= 1.25 and fitness >= 1.0 and turnover <= 0.7:
            print("\n" + "="*50)
            print(" BINGO! TÌM THẤY ALPHA PASS TIÊU CHÍ!")
            print("="*50)
            print(f"Công thức: {formula}")
            print(f"Settings:  {settings}")
            print(f"Sharpe:    {sharpe:.2f}")
            print(f"Fitness:   {fitness:.2f}")
            print(f"Turnover:  {turnover:.4f}")
            passed = True
            break
        else:
            print("Chưa đạt chuẩn (Sharpe>=1.25, Fitness>=1.0, Turnover<=0.7). Thử nghiệm tiếp...")
            
    if not passed:
        print("\nĐã quét hết danh sách nhưng chưa có cái nào pass hoàn toàn.")
        
    auto.stop()

if __name__ == "__main__":
    auto_optimize()
