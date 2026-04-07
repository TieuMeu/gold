import MetaTrader5 as mt5

def get_settings_ui():
    return [
        {"key": "snowball_risk_pct", "label": "Risk MỖI LỆNH (%) -> Nhập 30% như Excel", "type": "entry", "default": "30.0"},
        {"key": "snowball_pips", "label": "SL / TP (Số Pip Vàng)", "type": "entry", "default": "20.0"},
        {"key": "snowball_target", "label": "Mục Tiêu Chốt Lãi ($)", "type": "entry", "default": "1000.0"},
        {"key": "snowball_max_lot", "label": "Lot Tối Đa (An toàn)", "type": "entry", "default": "5.0"}
    ]

def get_preview_info(account_info, settings):
    try:
        risk_pct = float(settings.get("snowball_risk_pct", 30.0))
        pips = float(settings.get("snowball_pips", 20.0))
        target = float(settings.get("snowball_target", 1000.0))
        max_lot_limit = float(settings.get("snowball_max_lot", 5.0))
        
        balance = account_info.balance
        
        if balance >= target: return f"🎉 ĐÃ ĐẠT TARGET {target}$! Rút tiền thôi!"
        
        # Tính toán trước Ngân sách và Lot để hiển thị lên UI
        money_at_risk = balance * (risk_pct / 100)
        volume = round(money_at_risk / (pips * 10), 2)
        
        if volume < 0.01: volume = 0.01
        if volume > max_lot_limit: volume = max_lot_limit
        
        return f"🔥 Ngân sách: {money_at_risk:.2f}$ | 🎯 Dự kiến vào: {volume} Lot"
    except:
        return "⚠️ Lỗi hiển thị thông số!"

def calculate_risk(account_info, signal, current_price, settings):
    try:
        risk_pct = float(settings.get("snowball_risk_pct", 30.0))
        pips = float(settings.get("snowball_pips", 20.0))
        target = float(settings.get("snowball_target", 1000.0))
        max_lot_limit = float(settings.get("snowball_max_lot", 5.0))
    except:
        risk_pct, pips, target, max_lot_limit = 30.0, 20.0, 1000.0, 5.0

    balance = account_info.balance
    if balance >= target: return 0, 0, 0, "Đã đạt Target!"

    # 1. TÍNH VOLUME (LOT) CHUẨN XÁC THEO EXCEL
    money_at_risk = balance * (risk_pct / 100)
    volume = round(money_at_risk / (pips * 10), 2)
    if volume < 0.01: volume = 0.01
    if volume > max_lot_limit: volume = max_lot_limit

    # 2. BẢN VÁ LỖI CHẾT NGƯỜI: Cố định 1 Pip Vàng = $0.1
    symbol_info = mt5.symbol_info("XAUUSD")
    if symbol_info is None:
        actual_distance = pips * 0.1 # Phòng hờ mất kết nối tạm thời
    else:
        actual_distance = (pips * 0.1) + (symbol_info.spread * symbol_info.point)
    
    if signal == "BUY":
        sl, tp = current_price - actual_distance, current_price + actual_distance
    else: 
        sl, tp = current_price + actual_distance, current_price - actual_distance
        
    return volume, round(sl, 2), round(tp, 2), f"Snowball Risk {risk_pct}%"