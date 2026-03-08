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

def place_trade(symbol, action, volume, price, sl, tp, comment):
    """Hàm đặt lệnh chung"""
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": action,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 202699,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }
    result = mt5.order_send(request)
    return result