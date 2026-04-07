import pandas as pd
import numpy as np

def get_settings_ui():
    return [
        {"key": "rsi_period", "label": "Chu kỳ RSI", "type": "entry", "default": "14"},
        {"key": "rsi_ob", "label": "Mức Quá Mua (Sell)", "type": "entry", "default": "70"},
        {"key": "rsi_os", "label": "Mức Quá Bán (Buy)", "type": "entry", "default": "30"}
    ]

def get_preview_info(account_info, settings):
    try:
        p = int(settings.get("rsi_period", 14))
        ob = int(settings.get("rsi_ob", 70))
        os = int(settings.get("rsi_os", 30))
        return f"🔄 Chiến thuật: Đảo chiều RSI ({p}) | Đỉnh: {ob} - Đáy: {os}"
    except:
        return "⚠️ Lỗi hiển thị thông số RSI"

# Hàm tính toán RSI không cần dùng thư viện ngoài (Tối ưu cho Bot)
def calculate_rsi(series, period):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # Sử dụng Exponential Moving Average giống công thức gốc của Wilder
    ema_up = up.ewm(com=period-1, adjust=False).mean()
    ema_down = down.ewm(com=period-1, adjust=False).mean()
    
    rs = ema_up / ema_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze(df, settings):
    try:
        rsi_period = int(settings.get("rsi_period", 14))
        ob_level = int(settings.get("rsi_ob", 70))  # Ngưỡng Quá mua
        os_level = int(settings.get("rsi_os", 30))  # Ngưỡng Quá bán
    except:
        rsi_period, ob_level, os_level = 14, 70, 30

    if len(df) < rsi_period + 5:
        return None, "Đang gom đủ nến tính RSI..."

    # 1. Tính mảng giá trị RSI cho toàn bộ nến
    df['RSI'] = calculate_rsi(df['close'], rsi_period)

    # 2. Bắt tín hiệu tại cây nến VỪA ĐÓNG CỬA (tránh tín hiệu giả của nến đang chạy)
    prev_rsi = df.iloc[-3]['RSI'] # Nến trước đó
    curr_rsi = df.iloc[-2]['RSI'] # Nến vừa đóng xong

    signal = None
    comment = ""

    # 3. LOGIC KÍCH HOẠT VÀO LỆNH (Triggers)
    # Tín hiệu MUA (Quá Bán): Nếu nến trước RSI < 30 (bị ép quá mức) VÀ nến vừa đóng RSI vọt lên >= 30 (Dấu hiệu phục hồi)
    if prev_rsi < os_level and curr_rsi >= os_level:
        signal = "BUY"
        comment = f"RSI Phục hồi đáy: {curr_rsi:.1f} > {os_level}"
        
    # Tín hiệu BÁN (Quá Mua): Nếu nến trước RSI > 70 (hưng phấn quá mức) VÀ nến vừa đóng RSI tụt xuống <= 70 (Dấu hiệu hụt hơi)
    elif prev_rsi > ob_level and curr_rsi <= ob_level:
        signal = "SELL"
        comment = f"RSI Đảo chiều đỉnh: {curr_rsi:.1f} < {ob_level}"

    return signal, comment