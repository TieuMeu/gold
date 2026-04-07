import pandas as pd

def get_settings_ui():
    return [
        {"key": "ema_fast", "label": "Chu kỳ EMA Nhanh", "type": "entry", "default": "10"},
        {"key": "ema_slow", "label": "Chu kỳ EMA Chậm", "type": "entry", "default": "50"}
    ]

def get_preview_info(account_info, settings):
    fast = settings.get("ema_fast", 10)
    slow = settings.get("ema_slow", 50)
    return f"📈 Chiến thuật: Đánh theo Xu hướng (EMA {fast} cắt EMA {slow})"

# Hàm phân tích cốt lõi (Loader sẽ gọi hàm này mỗi khi có nến mới)
def analyze(df, settings):
    try:
        fast_period = int(settings.get("ema_fast", 10))
        slow_period = int(settings.get("ema_slow", 50))
    except:
        fast_period, slow_period = 10, 50

    # Nếu dữ liệu không đủ số nến để tính EMA chậm thì bỏ qua
    if len(df) < slow_period + 5:
        return None, "Đang gom đủ dữ liệu nến..."

    # 1. TÍNH TOÁN CHỈ BÁO (Toán học thuần túy)
    # Sử dụng thư viện pandas để tính Toán Exponential Moving Average (EMA)
    df['EMA_Fast'] = df['close'].ewm(span=fast_period, adjust=False).mean()
    df['EMA_Slow'] = df['close'].ewm(span=slow_period, adjust=False).mean()

    # 2. XÁC ĐỊNH VỊ TRÍ NẾN ĐỂ TRÁNH TÍN HIỆU GIẢ
    # Trong MT5, nến cuối cùng (df.iloc[-1]) là nến ĐANG CHẠY (giá nhảy liên tục).
    # Để chắc chắn, chúng ta chỉ lấy tín hiệu từ nến VỪA ĐÓNG CỬA (df.iloc[-2]) 
    # và nến TRƯỚC ĐÓ NỮA (df.iloc[-3]).
    
    prev_fast = df.iloc[-3]['EMA_Fast']
    prev_slow = df.iloc[-3]['EMA_Slow']
    
    curr_fast = df.iloc[-2]['EMA_Fast']
    curr_slow = df.iloc[-2]['EMA_Slow']

    signal = None
    comment = ""

    # 3. LOGIC GIAO CẮT (CROSSOVER)
    # Tín hiệu MUA (Golden Cross): Cây nến trước EMA nhanh nằm dưới, cây vừa đóng EMA nhanh vọt lên trên
    if prev_fast <= prev_slow and curr_fast > curr_slow:
        signal = "BUY"
        comment = f"Golden Cross: EMA {fast_period} > {slow_period}"
        
    # Tín hiệu BÁN (Death Cross): Cây nến trước EMA nhanh nằm trên, cây vừa đóng EMA nhanh cắm xuống dưới
    elif prev_fast >= prev_slow and curr_fast < curr_slow:
        signal = "SELL"
        comment = f"Death Cross: EMA {fast_period} < {slow_period}"

    return signal, comment