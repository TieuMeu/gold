import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from plugins.news_radar import is_market_safe

# KHÓA AN TOÀN
last_trade_time_mtf = None

def get_settings_ui():
    return [
        {"key": "strategy_scalp_mtf_magic", "label": "Mã Hộp (Magic Number)", "type": "entry", "default": "2002"},
        {"key": "mtf_bb_period", "label": "Chu kỳ BB (M5)", "type": "entry", "default": "20"},
        {"key": "mtf_bb_dev", "label": "Độ lệch BB (M5)", "type": "entry", "default": "2.0"},
        {"key": "mtf_rsi_period", "label": "Chu kỳ RSI (M5)", "type": "entry", "default": "14"},
        {"key": "mtf_ema_trend", "label": "Chu kỳ Trend (H1, H4)", "type": "entry", "default": "50"}
    ]

def get_preview_info(account_info, settings):
    magic = settings.get("strategy_scalp_mtf_magic", "2002")
    return f"🛡️ HỘP [{magic}]: M5 PRO (Bảo vệ H1/H4 + Né bão)"

def calculate_rsi(series, period):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period-1, adjust=False).mean()
    ema_down = down.ewm(com=period-1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def get_higher_timeframe_trend(symbol, timeframe, ema_period):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
    if rates is None or len(rates) < ema_period: return None
    df_htf = pd.DataFrame(rates)
    df_htf['close'] = df_htf['close']
    df_htf['EMA'] = df_htf['close'].ewm(span=ema_period, adjust=False).mean()
    if df_htf.iloc[-1]['close'] > df_htf.iloc[-1]['EMA']: return "UP"
    elif df_htf.iloc[-1]['close'] < df_htf.iloc[-1]['EMA']: return "DOWN"
    return "FLAT"

def analyze(df, settings):
    global last_trade_time_mtf
    
    # ---------------------------------------------------
    # 📡 GỌI RADAR KIỂM TRA BÃO TIN TỨC TRƯỚC TIÊN
    # ---------------------------------------------------
    is_safe, news_status = is_market_safe()
    if not is_safe:
        return None, news_status
    # ---------------------------------------------------

    try:
        bb_period = int(settings.get("mtf_bb_period", 20))
        bb_dev = float(settings.get("mtf_bb_dev", 2.0))
        rsi_period = int(settings.get("mtf_rsi_period", 14))
        ema_trend = int(settings.get("mtf_ema_trend", 50))
    except:
        bb_period, bb_dev, rsi_period, ema_trend = 20, 2.0, 14, 50

    if len(df) < bb_period + 5: return None, "Đợi nến M5..."
    
    current_candle_time = df.iloc[-1]['time']
    symbol = "XAUUSD" 

    trend_h1 = get_higher_timeframe_trend(symbol, mt5.TIMEFRAME_H1, ema_trend)
    trend_h4 = get_higher_timeframe_trend(symbol, mt5.TIMEFRAME_H4, ema_trend)
    if not trend_h1 or not trend_h4: return None, "Đang đồng bộ H1/H4..."

    macro_bullish = (trend_h1 == "UP" and trend_h4 == "UP")
    macro_bearish = (trend_h1 == "DOWN" and trend_h4 == "DOWN")

    df['SMA'] = df['close'].rolling(window=bb_period).mean()
    df['STD'] = df['close'].rolling(window=bb_period).std()
    df['Upper_BB'] = df['SMA'] + (df['STD'] * bb_dev)
    df['Lower_BB'] = df['SMA'] - (df['STD'] * bb_dev)
    df['RSI'] = calculate_rsi(df['close'], rsi_period)

    prev_close, prev_lower, prev_upper, prev_rsi = df.iloc[-3]['close'], df.iloc[-3]['Lower_BB'], df.iloc[-3]['Upper_BB'], df.iloc[-3]['RSI']
    curr_close, curr_lower, curr_upper, curr_rsi = df.iloc[-2]['close'], df.iloc[-2]['Lower_BB'], df.iloc[-2]['Upper_BB'], df.iloc[-2]['RSI']

    signal = None
    comment = f"Vĩ mô H1:{trend_h1}|H4:{trend_h4}"

    if macro_bullish and prev_close <= prev_lower and curr_close > curr_lower and curr_rsi > 30 and prev_rsi <= 30:
        signal = "BUY"
        comment = "MTF BUY: Thuận Trend"
    elif macro_bearish and prev_close >= prev_upper and curr_close < curr_upper and curr_rsi < 70 and prev_rsi >= 70:
        signal = "SELL"
        comment = "MTF SELL: Thuận Trend"

    # CHỐT CHẶN COOLDOWN
    if signal:
        if last_trade_time_mtf == current_candle_time:
            return None, "Đang chờ đóng nến M5 (Chống Spam)"
        last_trade_time_mtf = current_candle_time

    return signal, comment