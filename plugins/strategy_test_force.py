import pandas as pd

# Biến toàn cục để ghi nhớ việc "đã nổ súng hay chưa"
has_fired = False

def get_settings_ui():
    return [
        {"key": "test_magic", "label": "Mã Hộp (Magic Number)", "type": "entry", "default": "9999"}
    ]

def get_preview_info(account_info, settings):
    return "⚠️ BỘ TEST: Nhắm mắt bóp cò đúng 1 lệnh BUY rồi tự tắt."

def analyze(df, settings):
    global has_fired
    
    # Nếu chưa bắn lệnh nào -> Ra lệnh BUY ngay lập tức bất chấp thị trường
    if not has_fired:
        has_fired = True
        return "BUY", "TEST HỆ THỐNG THÀNH CÔNG!"
        
    # Nếu đã bắn rồi -> Trả về None để nằm im
    return None, "Đã test xong 1 lệnh. Vui lòng tắt Hộp này đi."