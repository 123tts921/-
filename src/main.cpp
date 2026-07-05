#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <SPI.h>
#include <WebServer.h>
#include "epd_w21.h"
#include "config.h"
#include <time.h>
#include "esp_task_wdt.h"

uint8_t imgBuf[EPD_BYTES];
WebServer server(80);
String espIP = "";
volatile bool pendingUpdate = false;

// ===== 显示 =====
void bufFlush() {
    SPI.begin(PIN_SCK, -1, PIN_MOSI, PIN_CS);
    SPI.beginTransaction(SPISettings(10000000, MSBFIRST, SPI_MODE0));
    pinMode(PIN_BUSY, INPUT);
    pinMode(PIN_RST, OUTPUT);
    pinMode(PIN_DC, OUTPUT);
    pinMode(PIN_CS, OUTPUT);
    epd_init();
    epd_draw_raw(imgBuf);
    epd_sleep();
}

// ===== HTTP 拉取图像 =====
bool tryFullUpdate() {
    HTTPClient http;
    http.begin(RAW_URL);
    http.setTimeout(30000);
    int code = http.GET();
    if (code != 200) { http.end(); return false; }

    WiFiClient* s = http.getStreamPtr();
    size_t t = 0;
    while (t < sizeof(imgBuf)) {
        server.handleClient();
        delay(1);
        int l = s->readBytes(imgBuf + t, sizeof(imgBuf) - t);
        if (l <= 0) break;
        t += l;
    }
    http.end();

    if (t != sizeof(imgBuf)) return false;
    bufFlush();
    return true;
}

// ===== Web 页面 =====
void handleUpdate() {
    server.send(200, "text/plain", "QUEUED\n");
    pendingUpdate = true;
}

void handleStatus() {
    time_t now = time(nullptr);
    struct tm* ti = localtime(&now);
    char tb[20];
    snprintf(tb, sizeof(tb), "%02d:%02d:%02d", ti->tm_hour, ti->tm_min, ti->tm_sec);
    String j = "{\"ip\":\"" + espIP + "\",\"wifi\":" + String(WiFi.status()==WL_CONNECTED) + ",\"time\":\"" + tb + "\"}";
    server.send(200, "application/json", j);
}

void handleRestart() {
    server.send(200, "text/plain", "OK\n");
    delay(500);
    ESP.restart();
}

void handleRoot() {
    String h = R"rawliteral(<!DOCTYPE html><html><head><meta charset='utf-8'>
<meta name='viewport' content='width=400,initial-scale=1'>
<title>InkSight</title><style>
body{font:15px sans-serif;background:#f0f2f5;padding:12px;text-align:center}
.card{background:#fff;border-radius:10px;padding:14px;margin:8px auto;max-width:360px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
h3{margin-bottom:8px}.row{display:flex;justify-content:space-between;padding:3px 0;font-size:13px;color:#666}
.row b{color:#333}.ok{color:#4CAF50}.fail{color:#f44336}
.btn{display:block;width:100%;padding:12px;margin:6px 0;border:0;border-radius:8px;font-size:15px;color:#fff;cursor:pointer}
.g{background:#4CAF50}.r{background:#f44336}
.log{font:11px monospace;color:#999;padding:6px;background:#f8f8f8;border-radius:4px;min-height:18px}
</style></head><body>
<div class='card'><h3>InkSight</h3>
<div class='row'><span>IP</span><b id='ip'>-</b></div>
<div class='row'><span>WiFi</span><b id='wifi'>-</b></div>
<div class='row'><span>Time</span><b id='time'>-</b></div>
</div>
<div class='card'>
<button class='btn g' onclick='doUpdate()'>Refresh Screen</button>
<button class='btn r' onclick='doRestart()'>Restart</button>
<div class='log' id='log'>Ready.</div>
</div>
<script>
function doUpdate(){document.getElementById('log').textContent='Updating...';
fetch('/update').then(r=>r.text()).then(t=>{document.getElementById('log').textContent=t.trim()+' - wait ~15s for screen refresh'})
.catch(e=>{document.getElementById('log').textContent='Error: '+e})}
function doRestart(){if(confirm('Restart?'))fetch('/restart')}
function refresh(){fetch('/status').then(r=>r.json()).then(d=>{
document.getElementById('ip').textContent=d.ip;
document.getElementById('wifi').textContent=d.wifi?'Connected':'Offline';
document.getElementById('wifi').className=d.wifi?'ok':'fail';
document.getElementById('time').textContent=d.time||'-'})}
refresh();setInterval(refresh,8000);
</script></body></html>)rawliteral";
    server.send(200, "text/html; charset=utf-8", h);
}

void setup() {
    Serial.begin(115200);
    delay(100);

    // 禁用看门狗，防止长时间刷屏导致重启
    disableCore0WDT();
    disableLoopWDT();

    Serial.println("\n=== InkSight ===");

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("WiFi");
    int r = 0;
    while (WiFi.status() != WL_CONNECTED && r < 30) {
        delay(500);
        Serial.print(".");
        r++;
    }
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println(" FAIL");
        return;
    }
    espIP = WiFi.localIP().toString();
    Serial.println(" OK " + espIP);

    configTime(8 * 3600, 0, "ntp.aliyun.com", "pool.ntp.org");

    server.on("/", handleRoot);
    server.on("/update", handleUpdate);
    server.on("/restart", handleRestart);
    server.on("/status", handleStatus);
    server.begin();
    Serial.println("Ready");
}

void loop() {
    server.handleClient();

    if (pendingUpdate) {
        pendingUpdate = false;
        Serial.println("Update start");
        if (tryFullUpdate()) {
            Serial.println("Update OK");
        } else {
            Serial.println("Update FAIL");
        }
    }

    delay(50);
}
