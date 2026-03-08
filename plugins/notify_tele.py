import requests
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import os

# Tên file để ghi nhớ giờ đã gửi (Nằm cạnh file plugin)
LOCK_FILE = "plugins/tele_spam_block.lock"

def get_settings_ui():
    return [
        {"key": "tele_token", "label": "Telegram Token", "type": "entry", "default": ""},
        {"key": "tele_chat_id", "label": "Chat ID", "type": "entry", "default": ""}
    ]

def get_preview_info(account_info, settings):
    chat_id = settings.get("tele_chat_id", "")
    return f"✅ Auto Report: ON -> {chat_id}" if chat_id else "⚠️ Chưa nhập Chat ID"

# --- HÀM 1: BÁO CÁO HÀNG GIỜ (ĐÃ FIX SPAM) ---
def on_tick(context):
    
    # 1. Lấy Config
    config = context["config"]
    token = config.get("tele_token", "")
    chat_id = config.get("tele_chat_id", "")
    if not token or not chat_id: return

    # 2. Đọc "Sổ Nam Tào" xem giờ này đã gửi chưa
    last_sent = -1
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                content = f.read().strip()
                if content: last_sent = int(content)
        except: pass

    # 3. Kiểm tra thời gian
    now = datetime.now()
    
    # Logic: Phút = 00 VÀ Giờ hiện tại KHÁC giờ đã ghi trong sổ
    if now.minute == 0 and now.hour != last_sent:
        
        # ==> GHI SỔ NGAY LẬP TỨC (Khóa Spam)
        try:
            with open(LOCK_FILE, "w") as f:
                f.write(str(now.hour))
        except: pass # Nếu lỗi ghi file thì bỏ qua, tránh crash
        
        # 4. Thu thập dữ liệu (Code cũ)
        acc = context["account"]
        balance = acc.balance
        equity = acc.equity
        positions = mt5.positions_get()
        run_count = len(positions) if positions else 0

        # Lấy lịch sử 1h
        one_hour_ago = now - timedelta(hours=1)
        history = mt5.history_deals_get(one_hour_ago, now)
        
        list_win = ""
        list_loss = ""
        total_pnl = 0.0
        count_win = 0
        count_loss = 0

        if history:
            for deal in history:
                if deal.entry == mt5.DEAL_ENTRY_OUT and deal.profit != 0:
                    total_pnl += deal.profit
                    close_time = datetime.fromtimestamp(deal.time).strftime('%H:%M')
                    money_str = f"${abs(deal.profit):,.2f}" # Lấy trị tuyệt đối để hiển thị đẹp
                    
                    if deal.profit > 0:
                        count_win += 1
                        list_win += f"  └ {close_time} (+{money_str})\n"
                    else:
                        count_loss += 1
                        list_loss += f"  └ {close_time} (-{money_str})\n"

        if not list_win: list_win = "  (Không có)\n"
        if not list_loss: list_loss = "  (Không có)\n"

        # 5. Tạo nội dung (Giao diện bạn đã duyệt)
        msg = (
            f"📊 <b>BÁO CÁO HOẠT ĐỘNG {now.hour}:00</b>\n"
            f"----------------------------------\n"
            f"💰 <b>Vốn:</b> {balance:,.2f} USD\n"
            f"📈 <b>Equity:</b> {equity:,.2f} USD\n\n"
            
            f"🏃 <b>Đang chạy ({run_count}):</b>\n"
            f"{'Wait...' if run_count > 0 else 'Không có'}\n\n"
            
            f"🏁 <b>Đã chốt 1h qua ({count_win + count_loss}):</b>\n"
            f"✅ <b>Lãi ({count_win}):</b>\n"
            f"{list_win}"
            f"❌ <b>Lỗ ({count_loss}):</b>\n"
            f"{list_loss}"
            f"----------------------------------\n"
            f"💵 <b>Tổng PnL: {total_pnl:+,.2f} USD</b>"
        )

        # 6. Gửi đi
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                          json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
            print(f"✅ [TELE] Đã gửi báo cáo {now.hour}:00")
        except: pass

# --- HÀM 2: BÁO TÍN HIỆU ---
def send_message(message, settings):
    token = settings.get("tele_token", "")
    chat_id = settings.get("tele_chat_id", "")
    if not token or not chat_id: return
    
    icon = "🔔"
    if "BUY" in message: icon = "🟢"
    elif "SELL" in message: icon = "🔴"
    
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      json={"chat_id": chat_id, "text": f"{icon} {message}"}, timeout=5)
    except: pass