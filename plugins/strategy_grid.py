import pandas as pd

# Biến toàn cục để ghi nhớ mốc giá giăng lưới gần nhất
last_grid_price = 0.0

def get_settings_ui():
    return [
        {"key": "grid_step", "label": "Khoảng cách Lưới (Pips)", "type": "entry", "default": "20.0"}
    ]

def get_preview_info(account_info, settings):
    step = settings.get("grid_step", "20.0")
    return f"🕸️ Chiến thuật Lưới (Grid): Rải đinh mỗi {step} Pips"

# Hàm phân tích cốt lõi
def analyze(df, settings):
    global last_grid_price
    
    try:
        grid_step_pips = float(settings.get("grid_step", 20.0))
    except:
        grid_step_pips = 20.0

    # Đối với Vàng (XAUUSD), 1 Giá (ví dụ từ 2000 lên 2001) = 10 Pips = 100 Points.
    # Quy đổi Pips sang mức chênh lệch giá thực tế của Vàng:
    # Ví dụ: Nhập 20 pips -> Bot sẽ chờ giá chạy đúng 2.0 USD (giá vàng) để vào lệnh.
    grid_step_price = grid_step_pips * 0.1 

    # Lấy giá trị nến đóng cửa gần nhất
    current_price = df.iloc[-2]['close']

    # 1. KHỞI TẠO MỐC LƯỚI ĐẦU TIÊN
    # Khi bot vừa bật lên, nó sẽ lấy giá hiện tại làm tâm lưới (mốc số 0)
    if last_grid_price == 0.0:
        last_grid_price = current_price
        return None, f"Đã giăng tâm lưới tại mốc giá: {current_price:.2f}"

    signal = None
    comment = ""

    # 2. TÍNH TOÁN KHOẢNG CÁCH TỪ GIÁ HIỆN TẠI ĐẾN MỐC LƯỚI
    distance = current_price - last_grid_price

    # 3. KÍCH HOẠT VÀO LỆNH VÀ DỜI LƯỚI
    # Trường hợp 1: Giá tăng mạnh chạm cạnh trên của lưới -> Đánh SELL chặn lại
    if distance >= grid_step_price:
        signal = "SELL"
        comment = f"Grid Top: +{grid_step_pips} pips"
        last_grid_price = current_price  # Cập nhật mốc lưới mới lên cao hơn
        
    # Trường hợp 2: Giá giảm sâu chạm cạnh dưới của lưới -> Đánh BUY đỡ lại
    elif distance <= -grid_step_price:
        signal = "BUY"
        comment = f"Grid Bottom: -{grid_step_pips} pips"
        last_grid_price = current_price  # Cập nhật mốc lưới mới xuống thấp hơn

    return signal, comment