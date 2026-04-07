import MetaTrader5 as mt5

def connect_mt5():
    """Kết nối đến MT5, trả về True/False"""
    if not mt5.initialize():
        return False, mt5.last_error()
    return True, None

def get_account_info():
    """Lấy thông tin tài khoản"""
    acc = mt5.account_info()
    if acc:
        return {"login": acc.login, "equity": acc.equity, "balance": acc.balance}
    return None

def get_open_positions(symbol, magic_number):
    """Lấy danh sách các lệnh đang mở của một Hộp cụ thể"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    # Lọc ra lệnh thuộc về magic_number này
    return [p for p in positions if p.magic == magic_number]

def place_trade(symbol, action, volume, price, sl, tp, comment, magic=202699):
    """Hàm đặt lệnh nâng cấp: Bắt giá thực, Auto-Filling, Cắt Comment và BẢO VỆ SPREAD"""
    # 1. Đánh thức cặp tiền để đảm bảo lấy được giá
    mt5.symbol_select(symbol, True)
    
    # 2. Lấy thông tin nội tại của cặp tiền và giá thực tế
    sym_info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    
    if not tick or not sym_info:
        error = mt5.last_error()
        print(f"❌ Lỗi lấy dữ liệu giá XAUUSD từ server: {error}")
        return error 
        
    # =========================================================
    # 🛡️ LỚP KHIÊN THÉP: BỘ LỌC CHỐNG GIÃN SPREAD (BÃO TIN TỨC)
    # =========================================================
    current_spread = sym_info.spread
    max_spread_allowed = 500 # Giới hạn an toàn: 40 Points (tương đương 4.0 Pips Vàng)
    
    if current_spread > max_spread_allowed:
        # Từ chối bóp cò và ném ra thông báo cho hệ thống
        return f"🔒 KHÓA CÒ: Spread đang giãn quá cao ({current_spread} > {max_spread_allowed}). Nghi ngờ có bão!"
    # =========================================================
        
    # Lấy giá Ask cho lệnh BUY, giá Bid cho lệnh SELL
    real_price = tick.ask if action == mt5.ORDER_TYPE_BUY else tick.bid
    
    # 3. CẮT NGẮN COMMENT: MT5 cấm comment dài quá 31 ký tự.
    safe_comment = str(comment)[:27]
    
    # =========================================================
    # 4. 🤖 AI AUTO-FILLING: Tự động hỏi sàn xem dùng chế độ nào
    # =========================================================
    filling_type = mt5.ORDER_FILLING_FOK # Mặc định
    
    if sym_info.filling_mode & 1:
        filling_type = mt5.ORDER_FILLING_FOK
    elif sym_info.filling_mode & 2:
        filling_type = mt5.ORDER_FILLING_IOC
    else:
        filling_type = mt5.ORDER_FILLING_RETURN
        
    # 5. Đóng gói lệnh chuẩn Exness
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": action,
        "price": float(real_price),
        "sl": float(sl),
        "tp": float(tp),
        "deviation": 20,
        "magic": int(magic),
        "comment": safe_comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_type,  
    }
    
    # 6. Gửi lệnh lên sàn
    result = mt5.order_send(request)
    
    # =========================================================
    # 🚨 MÁY ĐỌC BỆNH CHUYÊN SÂU LẮP TRỰC TIẾP TRÊN SERVER
    # =========================================================
    if result is None:
        error_code = mt5.last_error()
        print(f"\n[⚠️ LỖI NỘI BỘ] Phần mềm MT5 trên server chặn lệnh, chưa kịp gửi lên sàn!")
        print(f"👉 Mã lỗi: {error_code}")
        print(f"👉 Dữ liệu gửi đi: {request}\n")
        return error_code 
        
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"\n[🛑 SÀN TỪ CHỐI] Exness đã nhận nhưng không cho khớp lệnh!")
        print(f"👉 Mã lỗi Sàn: {result.retcode} - Ghi chú: {result.comment}\n")
        
    return result