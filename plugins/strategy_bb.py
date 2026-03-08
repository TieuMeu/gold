import pandas as pd

# 1. KHAI BÁO GIAO DIỆN
def get_settings_ui():
    return [
        {"key": "bb_period", "label": "Chu kỳ (Period)", "type": "entry", "default": "20"},
        {"key": "bb_dev", "label": "Độ lệch (Deviation)", "type": "entry", "default": "2.0"}
    ]

# 2. LOGIC CHÍNH
def analyze(df, settings=None):
    if settings is None: settings = {}
    try:
        period = int(settings.get("bb_period", 20))
        dev = float(settings.get("bb_dev", 2.0))
    except:
        period, dev = 20, 2.0

    if len(df) < period: return None, ""

    sma = df['close'].rolling(window=period).mean()
    std = df['close'].rolling(window=period).std()
    
    upper = sma + (dev * std)
    lower = sma - (dev * std)
    
    price = df.iloc[-2]['close']
    
    # So sánh giá với Band
    if price <= lower.iloc[-2]:
        return "BUY", f"BB({period},{dev}) Lower Touch"
        
    elif price >= upper.iloc[-2]:
        return "SELL", f"BB({period},{dev}) Upper Touch"

    return None, ""