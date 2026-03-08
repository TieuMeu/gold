import pandas as pd

# 1. KHAI BÁO GIAO DIỆN
def get_settings_ui():
    return [
        {"key": "ema_fast", "label": "EMA Nhanh (Fast)", "type": "entry", "default": "10"},
        {"key": "ema_slow", "label": "EMA Chậm (Slow)", "type": "entry", "default": "50"}
    ]

# 2. LOGIC CHÍNH
def analyze(df, settings=None):
    if settings is None: settings = {}
    try:
        # Lấy thông số từ giao diện
        p_fast = int(settings.get("ema_fast", 10))
        p_slow = int(settings.get("ema_slow", 50))
    except:
        p_fast, p_slow = 10, 50

    if len(df) < p_slow: return None, ""

    # Tính toán theo thông số người dùng nhập
    df['ema_fast'] = df['close'].ewm(span=p_fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=p_slow, adjust=False).mean()

    curr = df.iloc[-2]
    prev = df.iloc[-3]

    if prev['ema_fast'] <= prev['ema_slow'] and curr['ema_fast'] > curr['ema_slow']:
        return "BUY", f"EMA {p_fast}/{p_slow} Cross UP"

    elif prev['ema_fast'] >= prev['ema_slow'] and curr['ema_fast'] < curr['ema_slow']:
        return "SELL", f"EMA {p_fast}/{p_slow} Cross DOWN"

    return None, ""