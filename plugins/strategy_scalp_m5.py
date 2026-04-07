import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from plugins.news_radar import is_market_safe

def get_settings_ui():
    return [
        {"key": "strategy_scalp_m5_magic", "label": "Mã Hộp (Magic Number)", "type": "entry", "default": "1001"},
        {"key": "m5_bb_period", "label": "Chu kỳ BB (M5)", "type": "entry", "default": "20"},
        {"key": "m5_bb_dev", "label": "Độ lệch BB (M5)", "type": "entry", "default": "2.0"},
        {"key": "m5_rsi_period", "label": "Chu kỳ RSI (M5)", "type": "entry", "default": "14"},
        {"key": "m5_ema_trend", "label": "Chu kỳ Trend để Nhường (H1,H4)", "type": "entry", "default": "50"}
    ]

def get_preview_info(account_info, settings):
    magic = settings.get("strategy_scalp_m5_magic", "1001")
    return f"📦 HỘP [{magic}]: M5 Scalper (Chế độ ưu tiên nhường MTF)"

def calculate_rsi(series, period):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period-1, adjust=False).mean()
    ema_down = down.ewm(com=period-1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def get_higher_timeframe_trend(symbol, timeframe, ema_period):
    """Hàm này giúp M5 ngó xem Trend lớn đang là gì để biết đường nhường"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    if rates is None or len(rates) < ema_period: return None
    df_htf = pd.DataFrame(rates)
    df_htf['close'] = df_htf['close']
    df_htf['EMA'] = df_htf['close'].ewm(span=ema_period, adjust=False).mean()
    if df_htf.iloc[-1]['close'] > df_htf.iloc[-1]['EMA']: return "UP"
    elif df_htf.iloc[-1]['close'] < df_htf.iloc[-1]['EMA']: return "DOWN"
    return "FLAT"

def analyze(df, settings):
    # 1. Quét Radar tin tức
    is_safe, news_status = is_market_safe()
    if not is_safe: return None, news_status

    try:
        bb_period = int(settings.get("m5_bb_period", 20))
        bb_dev = float(settings.get("m5_bb_dev", 2.0))
        rsi_period = int(settings.get("m5_rsi_period", 14))
        ema_trend = int(settings.get("m5_ema_trend", 50))
    except:
        bb_period, bb_dev, rsi_period, ema_trend = 20, 2.0, 14, 50

    if len(df) < bb_period + 5: return None, "Đợi nến..."
    symbol = "XAUUSD"

    # =========================================================
    # 2. KIỂM TRA TREND ĐỂ QUYẾT ĐỊNH CÓ NHƯỜNG MTF KHÔNG
    # =========================================================
    trend_h1 = get_higher_timeframe_trend(symbol, mt5.TIMEFRAME_H1, ema_trend)
    trend_h4 = get_higher_timeframe_trend(symbol, mt5.TIMEFRAME_H4, ema_trend)
    
    macro_bullish = (trend_h1 == "UP" and trend_h4 == "UP")
    macro_bearish = (trend_h1 == "DOWN" and trend_h4 == "DOWN")
    # =========================================================

    df['SMA'] = df['close'].rolling(window=bb_period).mean()
    df['STD'] = df['close'].rolling(window=bb_period).std()
    df['Upper_BB'] = df['SMA'] + (df['STD'] * bb_dev)
    df['Lower_BB'] = df['SMA'] - (df['STD'] * bb_dev)
    df['RSI'] = calculate_rsi(df['close'], rsi_period)

    prev_close, prev_lower, prev_upper, prev_rsi = df.iloc[-3]['close'], df.iloc[-3]['Lower_BB'], df.iloc[-3]['Upper_BB'], df.iloc[-3]['RSI']
    curr_close, curr_lower, curr_upper, curr_rsi = df.iloc[-2]['close'], df.iloc[-2]['Lower_BB'], df.iloc[-2]['Upper_BB'], df.iloc[-2]['RSI']

    signal = None
    comment = ""

    # KỊCH BẢN MUA (BẮT ĐÁY)
    if prev_close <= prev_lower and curr_close > curr_lower and curr_rsi > 30 and prev_rsi <= 30:
        if macro_bullish:
            # Nếu Trend Tăng -> MTF chắc chắn sẽ bắn -> M5 từ chối bắn!
            return None, "Đã nhường lệnh BUY cho MTF" 
        signal = "BUY"
        comment = "Scalp M5: Cản tàu (Ngược Trend)"
        
    # KỊCH BẢN BÁN (BẮT ĐỈNH)
    elif prev_close >= prev_upper and curr_close < curr_upper and curr_rsi < 70 and prev_rsi >= 70:
        if macro_bearish:
            # Nếu Trend Giảm -> MTF chắc chắn sẽ bắn -> M5 từ chối bắn!
            return None, "Đã nhường lệnh SELL cho MTF"
        signal = "SELL"
        comment = "Scalp M5: Cản tàu (Ngược Trend)"

    return signal, comment