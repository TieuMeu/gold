import pandas as pd

def get_settings_ui():
    return [
        {"key": "rsi_period", "label": "Chu kỳ RSI (Mặc định 14)", "type": "entry", "default": "14"},
        {"key": "rsi_buy", "label": "Mức Mua (<)", "type": "entry", "default": "30"},
        {"key": "rsi_sell", "label": "Mức Bán (>)", "type": "entry", "default": "70"}
    ]

def calculate_rsi(series, period):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze(df, settings=None): # Thêm tham số settings
    if settings is None: settings = {}
    try:
        period = int(settings.get("rsi_period", 14))
        lv_buy = int(settings.get("rsi_buy", 30))
        lv_sell = int(settings.get("rsi_sell", 70))
    except:
        period, lv_buy, lv_sell = 14, 30, 70

    if len(df) < period + 5: return None, ""

    df['rsi'] = calculate_rsi(df['close'], period)
    curr = df.iloc[-2]
    
    if curr['rsi'] < lv_buy:
        return "BUY", f"RSI {curr['rsi']:.1f}"
    elif curr['rsi'] > lv_sell:
        return "SELL", f"RSI {curr['rsi']:.1f}"

    return None, ""