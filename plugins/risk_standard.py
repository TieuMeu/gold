import MetaTrader5 as mt5

# --- PHẦN BẮT BUỘC ĐỂ HIỆN GIAO DIỆN ---
def get_settings_ui():
    return [
        {"key": "risk_percent", "label": "Risk % (Tiền mất tối đa)", "type": "entry", "default": "1.0"},
        {"key": "sl_points", "label": "Stoploss (Points)", "type": "entry", "default": "2000"},
        {"key": "tp_points", "label": "Take Profit (Points)", "type": "entry", "default": "4000"}
    ]

# --- PHẦN PREVIEW ---
def get_preview_info(account_info, settings):
    try:
        risk = float(settings.get("risk_percent", 1.0))
        sl = int(settings.get("sl_points", 2000))
        balance = account_info.balance
        
        # Tính số tiền rủi ro tuyệt đối
        money_at_risk = balance * (risk / 100)
        
        return f"⚡ Vốn: {balance:,.2f}$ | Mất tối đa: {money_at_risk:,.2f}$ (khi chạm SL {sl} pts)"
    except:
        return "⚠️ Cần kết nối MT5 để tính"

# --- PHẦN TÍNH TOÁN (LÕI QUẢN TRỊ RỦI RO) ---
def calculate_risk(account_info, signal, current_price, settings):
    try:
        risk_pct = float(settings.get("risk_percent", 1.0))
        def_sl = int(settings.get("sl_points", 2000))
        def_tp = int(settings.get("tp_points", 4000))
    except:
        risk_pct, def_sl, def_tp = 1.0, 2000, 4000

    balance = account_info.balance
    symbol = "XAUUSD"
    
    # 1. Tính số tiền dám mất
    money_at_risk = balance * (risk_pct / 100)
    
    # 2. Lấy thông số nội tại của cặp Vàng trên sàn hiện tại
    sym_info = mt5.symbol_info(symbol)
    point = sym_info.point
    
    # Lấy giá trị tiền thật của 1 Point khi đánh 1 Lot (Thường XAUUSD là 1 USD)
    tick_value = sym_info.trade_tick_value 
    
    # 3. Tính toán Volume tự động co giãn theo Stoploss
    # Công thức: Lot = Tiền rủi ro / Số tiền mất của 1 Lot khi chạm SL
    loss_per_one_lot = def_sl * tick_value
    
    if loss_per_one_lot > 0:
        volume = round(money_at_risk / loss_per_one_lot, 2)
    else:
        volume = 0.01

    # Chặn Lot tối thiểu theo quy định của sàn
    if volume < 0.01: volume = 0.01

    # 4. Thiết lập SL/TP
    if signal == "BUY":
        sl = current_price - (def_sl * point)
        tp = current_price + (def_tp * point)
    else:
        sl = current_price + (def_sl * point)
        tp = current_price - (def_tp * point)
        
    return volume, round(sl, 3), round(tp, 3), f"Risk {risk_pct}% | Đánh {volume}L"