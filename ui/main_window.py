import customtkinter as ctk
import threading
import time
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import os
import sys

# IMPORT TRAY LIB
import pystray
from pystray import MenuItem as item
from PIL import Image 

# IMPORT CORE
from core import mt5_handler, utils

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class PenguLoader(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Gold Pro V7.0 (Multi-Sandbox)") # Lên đời version
        self.geometry("950x700")
        self.resizable(True, True)
        
        # KHI BẤM X -> ẨN XUỐNG TRAY
        self.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        
        if os.path.exists("gold.ico"): self.iconbitmap("gold.ico")
        
        self.global_config = utils.load_config()
        self.dynamic_inputs = {} 
        self.plugin_checkboxes = {}
        self.saved_states = {} 
        self.tray_icon = None

        # GUI SETUP
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        self.tab_home = self.tabview.add("Home")
        self.tab_plugins = self.tabview.add("Plugins & Settings")
        self.tab_logs = self.tabview.add("Logs")

        # TAB HOME
        self.frame_home = ctk.CTkFrame(self.tab_home, fg_color="transparent")
        self.frame_home.pack(fill="both", expand=True)
        ctk.CTkLabel(self.frame_home, text="QUANT KERNEL V7.0", font=("Roboto", 24, "bold")).pack(pady=20)
        self.lbl_status = ctk.CTkLabel(self.frame_home, text="SYSTEM STOPPED", font=("Arial", 16), text_color="gray")
        self.lbl_status.pack(pady=10)
        self.btn_power = ctk.CTkButton(self.frame_home, text="START ENGINE", height=60, width=250, 
                                       font=("Arial", 16, "bold"), fg_color="#27AE60", hover_color="#2ECC71",
                                       command=self.toggle_engine)
        self.btn_power.pack(pady=40)

        # TAB PLUGINS
        self.frame_left = ctk.CTkFrame(self.tab_plugins, width=300)
        self.frame_left.pack(side="left", fill="y", padx=10, pady=10)
        ctk.CTkButton(self.frame_left, text="📂 Folder Plugins", command=self.open_plugin_folder).pack(pady=5)
        ctk.CTkButton(self.frame_left, text="🔄 Reload (Giữ Tick)", fg_color="#D35400", command=self.reload_keep_state).pack(pady=5)
        self.scroll_plugins = ctk.CTkScrollableFrame(self.frame_left)
        self.scroll_plugins.pack(fill="both", expand=True, pady=10)

        self.frame_right = ctk.CTkFrame(self.tab_plugins)
        self.frame_right.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.scroll_settings = ctk.CTkScrollableFrame(self.frame_right, height=400)
        self.scroll_settings.pack(fill="x", expand=True, pady=5)
        
        self.footer_plugin = ctk.CTkFrame(self.frame_right, fg_color="#1A252F")
        self.footer_plugin.pack(side="bottom", fill="x", pady=10)
        ctk.CTkButton(self.footer_plugin, text="💾 LƯU CẤU HÌNH", height=35, command=self.save_visible_settings).pack(side="top", fill="x", padx=10, pady=10)
        
        self.switch_plugin_master = ctk.CTkSwitch(self.footer_plugin, text="DISABLED", font=("Arial", 16, "bold"),
                                                  onvalue="on", offvalue="off", progress_color="#3498DB",
                                                  command=self.toggle_perm)
        self.switch_plugin_master.pack(side="right", padx=20, pady=15)

        # TAB LOGS
        self.log_box = ctk.CTkTextbox(self.tab_logs)
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

        self.is_running = False
        self.refresh_system() 

    # --- HÀM UI ---
    def reload_keep_state(self):
        self.saved_states = {name: var.get() for name, var in self.plugin_checkboxes.items()}
        self.refresh_system()
        self.log("🔄 Reloaded System!")

    def refresh_system(self):
        for w in self.scroll_plugins.winfo_children(): w.destroy()
        self.plugin_checkboxes.clear()
        files = utils.scan_plugins()
        
        for f in files:
            mod = utils.load_plugin_module(f)
            if mod and hasattr(mod, "get_settings_ui"):
                is_checked = self.saved_states.get(f, False)
                var = ctk.BooleanVar(value=is_checked)
                chk = ctk.CTkCheckBox(self.scroll_plugins, text=f, variable=var, command=self.redraw_settings_panel)
                chk.pack(anchor="w", pady=5)
                self.plugin_checkboxes[f] = var
        self.redraw_settings_panel()

    def redraw_settings_panel(self):
        for w in self.scroll_settings.winfo_children(): w.destroy()
        self.dynamic_inputs.clear()

        for name, var in self.plugin_checkboxes.items():
            if var.get():
                mod = utils.load_plugin_module(name)
                if not mod:
                    continue

                group = ctk.CTkFrame(self.scroll_settings)
                group.pack(fill="x", pady=10, padx=5)
                ctk.CTkLabel(group, text=f"🔧 {name}", font=("Arial", 12, "bold"), text_color="#F39C12").pack(anchor="w", padx=10)

                if hasattr(mod, "get_settings_ui"):
                    for req in mod.get_settings_ui():
                        key = req["key"]
                        val = self.global_config.get(key, req["default"])
                        row = ctk.CTkFrame(group, fg_color="transparent")
                        row.pack(fill="x", pady=2)
                        ctk.CTkLabel(row, text=req["label"], width=150, anchor="w").pack(side="left")
                        entry = ctk.CTkEntry(row)
                        entry.insert(0, str(val))
                        entry.pack(side="right", fill="x", expand=True)
                        self.dynamic_inputs[key] = entry
                
                if hasattr(mod, "get_preview_info"):
                    acc = mt5.account_info() if mt5.initialize() else None
                    if acc:
                        try:
                            info = mod.get_preview_info(acc, self.global_config)
                            ctk.CTkLabel(group, text=f"ℹ️ {info}", text_color="#2ECC71", font=("Arial", 11)).pack(anchor="w", padx=10)
                        except: pass

    def save_visible_settings(self):
        for key, entry in self.dynamic_inputs.items():
            self.global_config[key] = entry.get()
        utils.save_config(self.global_config)
        self.log(f"✅ Đã lưu cấu hình!")
        if self.is_running: self.redraw_settings_panel()

    def toggle_perm(self):
        txt = "ENABLED" if self.switch_plugin_master.get() == "on" else "DISABLED"
        self.switch_plugin_master.configure(text=txt)

    def toggle_engine(self):
        if self.is_running:
            self.is_running = False
            self.btn_power.configure(text="START ENGINE", fg_color="#27AE60")
            self.lbl_status.configure(text="SYSTEM STOPPED", text_color="gray")
            return

        ok, err = mt5_handler.connect_mt5()
        if not ok:
            self.log(f"❌ MT5 Error: {err}")
            return

        self.is_running = True
        self.btn_power.configure(text="STOP ENGINE", fg_color="#C0392B")
        self.lbl_status.configure(text=f"CONNECTED: {mt5.account_info().login}", text_color="#00E676")
        self.redraw_settings_panel()
        threading.Thread(target=self.run_loop).start()

    def run_loop(self):
        symbol = "XAUUSD"
        while self.is_running:
            try:
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100) # Đã ép cứng về M5
                acc_info = mt5.account_info()
                
                current_price = 0
                if rates is not None:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    current_price = df.iloc[-1]['close']
                    
                    try:
                        if self.state() == "normal":
                            self.title(f"Gold Pro V7.0 (Multi-Sandbox) - {current_price}")
                    except: pass
                
                active_plugins = []
                for name, var in self.plugin_checkboxes.items():
                    if var.get():
                        mod = utils.load_plugin_module(name)
                        if mod: active_plugins.append(mod)

                if acc_info:
                    context = {
                        "account": acc_info,
                        "price": current_price,
                        "df": df if rates is not None else None,
                        "config": self.global_config,
                        "permission": self.switch_plugin_master.get() == "on"
                    }
                    for mod in active_plugins:
                        if hasattr(mod, "on_tick"):
                            mod.on_tick(context)

                # ========================================================
                # LÕI XỬ LÝ HỘP RIÊNG (SANDBOX - MAGIC NUMBER)
                # ========================================================
                if rates is not None and self.switch_plugin_master.get() == "on":
                    strats = [m for m in active_plugins if hasattr(m, "analyze")]
                    risks = [m for m in active_plugins if hasattr(m, "calculate_risk")]
                    notifies = [m for m in active_plugins if hasattr(m, "send_message")]

                    for s in strats:
                        mod_name = s.__name__.split('.')[-1]
                        
                        # Đọc Magic từ config, nếu người dùng chưa cài thì tự sinh ra 1 số cố định
                        magic = int(self.global_config.get(f"{mod_name}_magic", 200000 + abs(hash(mod_name)) % 10000))
                        
                        # [CHỐT CHẶN] - Kiểm tra xem Hộp này đang có lệnh gồng không?
                        open_pos = mt5_handler.get_open_positions(symbol, magic)
                        if open_pos and len(open_pos) > 0:
                            # Hộp đang có lệnh, bỏ qua không cho phân tích nến nữa (Chống nhồi lệnh)
                            continue 
                        
                        # Nếu rảnh rỗi, Hộp được phép phân tích biểu đồ
                        sig, cmt = s.analyze(df.copy(), self.global_config)
                        
                        if sig:
                            vol, sl, tp, r_cmt = 0.01, 0, 0, ""
                            if risks:
                                # Risk hiện tại vẫn dùng chung công thức, bài sau ta sẽ tách Risk ra
                                vol, sl, tp, r_cmt = risks[0].calculate_risk(acc_info, sig, current_price, self.global_config)
                            
                            full_cmt = f"[{mod_name}] {cmt} | {r_cmt}"
                            action = mt5.ORDER_TYPE_BUY if sig=="BUY" else mt5.ORDER_TYPE_SELL
                            
                            # Gửi lệnh lên sàn kèm thẻ Căn Cước (Magic Number)
                            res = mt5_handler.place_trade(symbol, action, vol, current_price, sl, tp, full_cmt, magic)
                            
                            # Xử lý kết quả trả về đa định dạng siêu chuẩn
                            if res and hasattr(res, 'retcode'):
                                if res.retcode == mt5.TRADE_RETCODE_DONE:
                                    msg = f"✅ HỘP [{magic}] VÀO LỆNH: {sig} {vol}L | {full_cmt}"
                                    self.log(msg)
                                    for n in notifies: n.send_message(msg, self.global_config)
                                else:
                                    self.log(f"🛑 SÀN TỪ CHỐI! Mã: {res.retcode} - Ghi chú: {res.comment}")
                            
                            elif type(res) is tuple:
                                self.log(f"⚠️ MT5 CHẶN TỪ CỬA! Mã lỗi gốc: {res}")
                                
                            elif type(res) is str:
                                # Dùng để in ra các cảnh báo bằng chữ (VD: Lỗi giãn Spread)
                                self.log(f"🛡️ HỆ THỐNG CHẶN: {res}")
                                
                            else:
                                # Bắt sống mọi thể loại dữ liệu dị thường
                                self.log(f"❓ LỖI KHÔNG XÁC ĐỊNH LỌT LƯỚI! Dữ liệu thô: {res}")
                
                time.sleep(1)
            except Exception as e:
                self.log(f"Err: {e}")
                time.sleep(5)

    def open_plugin_folder(self):
        try: os.startfile(os.path.abspath("plugins"))
        except: pass
    
    def log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        self.after(0, lambda: self.log_box.insert("end", f"[{t}] {msg}\n") or self.log_box.see("end"))
    
    def show_window(self, icon, item):
        self.tray_icon.stop() 
        self.after(0, self.deiconify) 

    def quit_app(self, icon, item):
        self.tray_icon.stop()
        self.is_running = False
        self.quit()
        sys.exit()

    def hide_to_tray(self):
        self.withdraw()
        if os.path.exists("gold.ico"): image = Image.open("gold.ico")
        else: image = Image.new('RGB', (64, 64), color = 'red')
        menu = (item('Hiện Bot', self.show_window), item('Thoát', self.quit_app))
        self.tray_icon = pystray.Icon("GoldBot", image, "Gold Pro Running...", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()