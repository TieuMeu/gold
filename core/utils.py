import json
import os
import sys  # <--- ĐÂY LÀ THỨ CÒN THIẾU
import importlib.util
import traceback 

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: return json.load(f)
        except: pass
    return {}

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Lỗi lưu config: {e}")

def scan_plugins(folder="plugins"):
    if not os.path.exists(folder):
        os.makedirs(folder)
        return []
    # Loại bỏ file __init__, file rác và file bác sĩ nếu lỡ còn sót
    files = [f for f in os.listdir(folder) if f.endswith(".py") and f != "__init__.py" and not f.startswith("bac_si")]
    return sorted(files)

def load_plugin_module(filename, folder="plugins"):
    try:
        module_name = filename[:-3]
        path = os.path.join(folder, filename)
        
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None:
            print(f"❌ [UTILS] Không thể tìm thấy spec cho {filename}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module # Đăng ký module (Cần import sys ở trên)
        spec.loader.exec_module(module)
        
        return module

    except Exception as e:
        print(f"\n{'='*30}")
        print(f"❌ LỖI NGHIÊM TRỌNG KHI LOAD: {filename}")
        print(f"👉 Chi tiết lỗi: {e}")
        traceback.print_exc()
        print(f"{'='*30}\n")
        return None