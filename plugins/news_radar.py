import requests
from datetime import datetime, timedelta, timezone

# Bộ nhớ đệm (Cache) để Bot không phải tải lại web liên tục làm chậm tốc độ bóp cò
_cached_news = []
_last_fetch_time = None

def get_usd_high_impact_news():
    global _cached_news, _last_fetch_time
    now_utc = datetime.now(timezone.utc)
    
    # Cập nhật tin tức 4 tiếng 1 lần
    if _last_fetch_time is None or (now_utc - _last_fetch_time).total_seconds() > 14400:
        # API JSON chính thức của ForexFactory
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        try:
            # Chỉ cho phép web tải trong 5 giây, nếu lag quá thì bỏ qua để không kẹt Bot
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                _cached_news = response.json()
                _last_fetch_time = now_utc
        except:
            pass 
            
    return _cached_news

def is_market_safe():
    news_data = get_usd_high_impact_news()
    if not news_data:
        # Mặc định an toàn nếu ForexFactory bảo trì
        return True, "Trời quang mây tạnh" 
        
    now_utc = datetime.now(timezone.utc)
    
    for event in news_data:
        # Chỉ quan tâm tin USD và mức độ Cao (High Impact)
        if event.get('country') == 'USD' and event.get('impact') == 'High':
            news_time_str = event.get('date')
            try:
                # Ép kiểu thời gian của ForexFactory về chuẩn máy chủ hiện tại
                news_time = datetime.fromisoformat(news_time_str)
                news_time_utc = news_time.astimezone(timezone.utc)
                
                # BÁN KÍNH NGUY HIỂM: Trước 30 phút và Sau 30 phút
                danger_start = news_time_utc - timedelta(minutes=30)
                danger_end = news_time_utc + timedelta(minutes=30)
                
                # Nếu thời gian hiện tại nằm trong vùng bão -> Báo động đỏ!
                if danger_start <= now_utc <= danger_end:
                    return False, f"⚠️ Núp bão: {event.get('title')}"
            except:
                continue
                
    return True, "Trời quang mây tạnh"