"""
InkSight 一键刷新工具
1. 启动 server.py（不自动关闭）
2. 等待就绪
3. 触发 ESP32 更新
4. 等待 ESP32 完成刷新
5. 关闭 server.py
"""
import sys, os, subprocess, time, requests, traceback, socket

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "refresh_log.txt")

def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def wait_for_server(url, timeout=15):
    """等待 server.py 就绪"""
    for i in range(timeout):
        try:
            r = requests.get(url, timeout=2, proxies={"http": None, "https": None})
            return True
        except:
            time.sleep(1)
    return False

def wait_for_esp32(ip, timeout=10):
    """等待 ESP32 在线"""
    for i in range(timeout):
        try:
            r = requests.get(f"http://{ip}/status", timeout=3, proxies={"http": None, "https": None})
            return True
        except:
            time.sleep(1)
    return False

try:
    BASE = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(BASE, "config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)
    ESP_IP = config.get("esp_ip", "192.168.3.62")
    PC_IP = config.get("pc_ip", "127.0.0.1")
    SERVER_PORT = int(config.get("server_port", 8080))
    ESP = f"http://{ESP_IP}"
    SERVER_URL = f"http://{PC_IP}:{SERVER_PORT}/"

    # 先检查 server.py 是否已在运行
    log("1/4 检查 server.py ...")
    server_proc = None
    try:
        r = requests.get(SERVER_URL, timeout=2, proxies={"http": None, "https": None})
        log("   server.py 已在运行")
    except:
        log("   启动 server.py ...")
        server_proc = subprocess.Popen(
            [sys.executable, os.path.join(BASE, "server.py")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log(f"   PID: {server_proc.pid}")
        if not wait_for_server(SERVER_URL):
            log("   ERROR: server.py 启动失败")
            os.system("pause"); sys.exit(1)
        log("   server.py 就绪")

    # 检查 ESP32 在线
    log("2/4 检查 ESP32 ...")
    if not wait_for_esp32(ESP_IP):
        log("   ERROR: ESP32 离线，请确认供电正常")
        os.system("pause"); sys.exit(1)
    log("   ESP32 在线")

    # 触发更新
    log("3/4 触发更新 ...")
    for attempt in range(3):
        try:
            r = requests.get(f"{ESP}/update", timeout=15, proxies={"http": None, "https": None})
            log(f"   Response: {r.text.strip()}")
            break
        except requests.exceptions.Timeout:
            log(f"   超时，重试 ({attempt+1}/3)...")
            time.sleep(5)
    else:
        log("   多次超时，但更新可能已在进行中")

    # 等待屏幕刷新完成
    log("4/4 等待屏幕刷新 (~45s) ...")
    time.sleep(45)

    # 检查 ESP32 是否还活着（刷新期间 WiFi 会短暂无响应）
    ok = False
    for i in range(6):
        try:
            r = requests.get(f"{ESP}/status", timeout=5, proxies={"http": None, "https": None})
            log(f"   ESP32: {r.text.strip()}")
            ok = True
            break
        except:
            log(f"   ESP32 暂时无响应，继续等待 ({i+1}/6)...")
            time.sleep(10)
    if ok:
        log("DONE!")
    else:
        log("   已触发刷新，但 ESP32 暂时未恢复；请看屏幕是否已更新")

    # 关闭我们启动的 server.py
    if server_proc:
        log("   关闭 server.py ...")
        server_proc.terminate()
        server_proc.wait(timeout=5)

except Exception as e:
    log(f"ERROR: {e}")
    log(traceback.format_exc())

log("按任意键关闭...")
try:
    input()
except:
    pass
