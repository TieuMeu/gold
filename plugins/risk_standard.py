import MetaTrader5 as mt5

# --- PHẦN BẮT BUỘC ĐỂ HIỆN GIAO DIỆN ---
def get_settings_ui():
    return [
        {"key": "risk_percent", "label": "Risk % (Ví dụ: 1.0)", "type": "entry", "default": "1.0"},
        {"key": "sl_points", "label": "Stoploss (Points)", "type": "entry", "default": "2000"},
        {"key": "tp_points", "label": "Take Profit (Points)", "type": "entry", "default": "4000"}
    ]

# --- PHẦN PREVIEW ---
def get_preview_info(account_info, settings):
    try:
        risk = float(settings.get("risk_percent", 1.0))
        balance = account_info.balance
        # Tính Lot: Vốn / 100k * Risk
        lot = round((balance / 100000) * risk, 2)
        if lot < 0.01: lot = 0.01
        return f"⚡ Vốn: {balance}$ | Risk: {risk}% => Lot dự tính: {lot}"
    except:
        return "⚠️ Cần kết nối MT5 để tính Lot"

# --- PHẦN TÍNH TOÁN ---
def calculate_risk(account_info, signal, current_price, settings):
    try:
        risk_pct = float(settings.get("risk_percent", 1.0))
        def_sl = int(settings.get("sl_points", 2000))
        def_tp = int(settings.get("tp_points", 4000))
    except:
        risk_pct, def_sl, def_tp = 1.0, 2000, 4000

    balance = account_info.balance
    volume = round((balance / 100000) * risk_pct, 2)
    if volume < 0.01: volume = 0.01

    point = mt5.symbol_info("XAUUSD").point
    
    if signal == "BUY":
        sl = current_price - (def_sl * point)
        tp = current_price + (def_tp * point)
    else:
        sl = current_price + (def_sl * point)
        tp = current_price - (def_tp * point)
        
    return volume, sl, tp, f"Risk {risk_pct}%"