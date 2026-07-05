import io, os, re, json, requests
from datetime import datetime
from flask import Flask, Response
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

WEATHER_URL = CONFIG["weather_url"]
API_TOKEN = CONFIG.get("api_token", "")
TASK_FILE = CONFIG["task_file"]
NAILONG = os.path.join(BASE_DIR, CONFIG.get("asset_image", "nailong.png.jpg"))
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

W, H = 400, 300
B, WHT, YEL, RED = 0, 1, 2, 3

FONT_PATH = None
for p in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]:
    if os.path.exists(p): FONT_PATH = p; break

_fc = {}
def gf(s):
    if not FONT_PATH: return ImageFont.load_default()
    if s not in _fc: _fc[s] = ImageFont.truetype(FONT_PATH, s)
    return _fc[s]

def th(text, font):
    """文字实际高度"""
    b = ImageDraw.Draw(Image.new("1", (1, 1))).textbbox((0, 0), "测试", font=font)
    return b[3] - b[1]

def tw(text, font):
    """文字实际宽度"""
    return ImageDraw.Draw(Image.new("1", (1, 1))).textlength(text, font=font)

def fetch_w():
    try:
        r = requests.get(WEATHER_URL, headers=HEADERS, timeout=5)
        return r.json() if r.status_code==200 else None
    except: return None

def read_tasks():
    ts = []
    try:
        with open(TASK_FILE, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^\s*[-*]\s*\[([ xX])\]\s*(.+)", line)
                if not m or m.group(1)!=" ": continue
                rw = m.group(2)
                p = 3
                if "⏫" in rw: p=0
                elif "🔺" in rw: p=1
                elif "🔼" in rw: p=2
                elif "🔽" in rw or "⏬" in rw: p=4
                sd = re.search(r'🛫\s*(\d{4})-(\d{2})-(\d{2})', rw)
                st = f"{sd.group(2)}-{sd.group(3)}" if sd else ""
                dd = re.search(r'📅\s*(\d{4})-(\d{2})-(\d{2})', rw)
                dl = f"{dd.group(2)}-{dd.group(3)}" if dd else ""
                tx = rw
                for pt in [r'[⏫🔺🔼🔽⏬]', r'🛫\s*\S+', r'📅\s*\S+', r'[⏳✅]']:
                    tx = re.sub(pt, '', tx)
                tx = tx.strip()
                if tx: ts.append((tx, p, st, dl))
    except: pass
    ts.sort(key=lambda x: x[1])
    return ts

def trunc(s, f, w):
    if tw(s, f) <= w: return s
    while s and tw(s+"..", f) > w: s = s[:-1]
    return s+".."

def load_img(path, tw_img, th_img, palette):
    if os.path.exists(path):
        try:
            im = Image.open(path).convert("RGB")
            im.thumbnail((tw_img, th_img), Image.LANCZOS)
            pl = Image.new("P", (1,1))
            pl.putpalette(palette)
            return im.quantize(palette=pl, dither=Image.FLOYDSTEINBERG)
        except: pass
    return None

def render():
    pal = [0,0,0, 255,255,255, 255,255,0, 255,0,0] + [0]*756
    img = Image.new("P", (W, H), WHT)
    img.putpalette(pal)
    d = ImageDraw.Draw(img)

    wd = fetch_w()
    ts = read_tasks()
    now = datetime.now()

    LX = 130
    BX = 3
    P = 6

    d.rectangle([(BX,BX),(W-BX-1,H-BX-1)], outline=B, width=2)
    d.line([(LX, BX+2), (LX, H-BX-2)], fill=B, width=2)

    # ===== 左栏 =====
    x = BX + P
    lw = LX - x - P  # 可用宽度

    # 日期
    d.text((x, 4), now.strftime('%m'), font=gf(26), fill=RED)
    d.text((x+32, 6), "月", font=gf(12), fill=B)
    d.text((x, 28), now.strftime('%d'), font=gf(34), fill=B)
    wds = ["周一","周二","周三","周四","周五","周六","周日"]
    wd_name = wds[now.weekday()]
    d.text((x+38, 54), wd_name, font=gf(11), fill=RED)
    d.line([(x, 70), (LX-P, 70)], fill=B, width=1)

    # 天气
    wy = 76
    if wd:
        t = wd.get("temperature","?")
        w = wd.get("weather","?")
        h = wd.get("humidity","?")
        wi = wd.get("wind_direction","")+wd.get("wind_power","")
        fc = wd.get("forecast",[])
        td = fc[0] if fc else {}
        tm = fc[1] if len(fc)>1 else {}

        wl = w.lower()
        if any(k in wl for k in ["雨","rain"]):
            d.ellipse([(x,wy+4),(x+10,wy+14)], outline=B)
            d.ellipse([(x+10,wy),(x+20,wy+10)], outline=B)
        elif any(k in wl for k in ["雪","snow"]):
            d.ellipse([(x,wy+4),(x+10,wy+14)], outline=B)
            d.ellipse([(x+8,wy),(x+18,wy+10)], outline=B)
        elif any(k in wl for k in ["云","cloud","阴","多云"]):
            d.ellipse([(x,wy+6),(x+12,wy+16)], outline=B)
            d.ellipse([(x+6,wy+2),(x+20,wy+14)], outline=B)
        else:
            d.ellipse([(x+1,wy+3),(x+13,wy+15)], outline=B)
            d.ellipse([(x+3,wy+5),(x+11,wy+13)], fill=YEL)

        d.text((x+22, wy), f"{t}°", font=gf(28), fill=RED)
        wy += 32
        d.text((x, wy), trunc(w, gf(13), lw), font=gf(13), fill=B)
        wy += 16

        if td.get("weather_day") and wy < 142:
            s = trunc(f"今:{td['weather_day']} {td.get('temp_min','?')}~{td.get('temp_max','?')}°", gf(10), lw)
            d.text((x, wy), s, font=gf(10), fill=B)
            wy += 13
        if tm.get("weather_day") and wy < 160:
            s = trunc(f"明:{tm['weather_day']} {tm.get('temp_min','?')}~{tm.get('temp_max','?')}°", gf(10), lw)
            d.text((x, wy), s, font=gf(10), fill=B)

    # 奶龙 大一些
    nl = load_img(NAILONG, lw, H-8, pal)
    if nl:
        img.paste(nl, (x, max(175, H-nl.height-6)))

    # ===== 右栏：任务清单 =====
    rx = LX + P
    rw = W - rx - P

    d.line([(rx, 4), (rx+rw, 4)], fill=RED, width=3)
    d.line([(rx, 22), (rx+rw, 22)], fill=RED, width=1)
    d.text((rx+2, 6), "任务清单", font=gf(14), fill=B)
    rt = 28

    ft = gf(13)
    fd = gf(9)

    for title, prio, st, dl in ts:
        # 每个任务约需 28-33px
        if rt + 32 > H - 6: break
        d.rectangle([(rx, rt+2), (rx+9, rt+11)], outline=RED, width=1)
        safe = trunc(title, ft, rw-13)
        d.text((rx+13, rt), safe, font=ft, fill=B)
        rt += th(title, ft) + 3
        if st or dl:
            line = f"{st} → {dl}" if st and dl else (st or dl)
            d.text((rx+13, rt), line, font=fd, fill=RED)
            rt += th(line, fd) + 2
        else:
            rt += 2
        if rt > H - 8: break

    raw = bytearray(W*H//4)
    for y in range(H):
        for x in range(0, W, 4):
            b = 0
            for i in range(4):
                b |= (img.getpixel((x+i,y))&3) << (6-i*2)
            raw[y*(W//4)+x//4] = b
    return bytes(raw)

@app.route("/raw")
def raw():
    return Response(render(), mimetype="application/octet-stream")

@app.route("/push")
def push():
    """渲染图像并通过 TCP 直接推送到 ESP32"""
    from flask import make_response
    import socket
    ESP_IP = "192.168.3.62"
    ESP_PORT = 8081
    raw_data = render()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((ESP_IP, ESP_PORT))
        s.sendall(raw_data)
        s.close()
        resp = make_response(f"PUSH OK ({len(raw_data)} bytes)\n")
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except Exception as e:
        resp = make_response(f"PUSH ERROR: {e}\n")
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

@app.route("/")
def index():
    return "OK"

if __name__ == "__main__":
    import sys, threading
    auto_close = 0
    if "--auto-close" in sys.argv:
        idx = sys.argv.index("--auto-close")
        auto_close = int(sys.argv[idx+1]) if idx+1 < len(sys.argv) else 120

    pc_ip = CONFIG.get("pc_ip", "0.0.0.0")
    port = int(CONFIG.get("server_port", 8080))
    print(f"Server: http://{pc_ip}:{port}")
    if auto_close:
        def closer():
            import time
            time.sleep(auto_close)
            print("Auto-closing server...")
            os._exit(0)
        threading.Thread(target=closer, daemon=True).start()
    app.run(host="0.0.0.0", port=port, debug=False)
