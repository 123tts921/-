# InkSight 墨水屏桌面助手

InkSight 是一个基于 ESP32-C3 与 4.2 寸四色墨水屏的桌面信息显示项目。电脑端负责读取 Obsidian 任务、获取天气并渲染为墨水屏原始图像；ESP32 通过 WiFi 拉取图像并刷新屏幕。

## 功能

- 显示日期、星期、天气、今日/明日预报
- 读取 Obsidian Markdown 任务清单
- 支持任务优先级与日期信息展示
- 桌面一键刷新：双击批处理脚本即可通过 WiFi 更新墨水屏
- ESP32 提供 `/status`、`/update`、`/restart` 接口

## 硬件

- ESP32-C3 开发板
- 4.2 寸 400×300 四色墨水屏，示例适配 GDEM042F52 类屏幕
- 稳定 5V/3.3V 供电

默认引脚见 [epd_w21.h](src/epd_w21.h)：

| ESP32-C3 | 墨水屏 |
|---|---|
| GPIO4 | SCK |
| GPIO6 | MOSI/SDA |
| GPIO7 | CS |
| GPIO1 | DC |
| GPIO2 | RST |
| GPIO10 | BUSY |
| 3V3 | VCC |
| GND | GND |

## 项目结构

```text
.
├── src/
│   ├── main.cpp              # ESP32 固件主程序
│   ├── epd_w21.cpp           # 墨水屏驱动
│   ├── epd_w21.h             # 屏幕参数与引脚
│   └── config.example.h      # ESP32 配置示例
├── server.py                 # Python 渲染服务
├── refresh.py                # PC 一键刷新脚本
├── config.example.json       # Python 配置示例
├── requirements.txt          # Python 依赖
├── platformio.ini            # PlatformIO 配置
└── nailong.png.jpg           # 示例素材
```

## 配置

### 1. Python 配置

复制示例配置：

```powershell
copy config.example.json config.json
```

编辑 `config.json`：

```json
{
  "weather_url": "https://uapis.cn/api/v1/misc/weather?city=北京大兴&forecast=true&indices=true&lang=zh",
  "api_token": "YOUR_UAPIS_TOKEN",
  "task_file": "D:\\path\\to\\QuickCapture.md",
  "asset_image": "nailong.png.jpg",
  "esp_ip": "192.168.3.62",
  "pc_ip": "192.168.3.15",
  "server_port": 8080
}
```

说明：

- `api_token`：天气 API Token，请不要提交到 GitHub
- `task_file`：Obsidian 任务 Markdown 文件路径
- `esp_ip`：ESP32 在局域网中的 IP
- `pc_ip`：运行 `server.py` 的电脑局域网 IP

### 2. ESP32 配置

复制示例配置：

```powershell
copy src\config.example.h src\config.h
```

编辑 `src/config.h`：

```cpp
#pragma once

#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"
#define RAW_URL "http://YOUR_PC_IP:8080/raw"
```

`config.json` 和 `src/config.h` 已加入 `.gitignore`，避免公开 WiFi 密码、Token 和本地路径。

## 安装依赖

```powershell
pip install -r requirements.txt
```

## 编译与烧录

安装 PlatformIO 后执行：

```powershell
pio run -t upload
```

如果 ESP32-C3 需要手动进入下载模式：按住 BOOT，按一下 RST/EN，再松开 BOOT。

## 日常使用

### 启动服务

```powershell
python server.py
```

浏览器访问：

```text
http://<PC_IP>:8080/
```

返回 `OK` 表示服务可用。

### 一键刷新

```powershell
python refresh.py
```

流程：

1. 检查或启动 `server.py`
2. 检查 ESP32 `/status`
3. 请求 ESP32 `/update`
4. ESP32 从 `RAW_URL` 拉取 `/raw` 图像并刷新墨水屏
5. 刷新完成后关闭由脚本启动的 `server.py`

Windows 桌面可以创建一个 `.bat` 调用 `refresh.py`，实现双击刷新。

## ESP32 接口

| 接口 | 说明 |
|---|---|
| `/` | 控制面板页面 |
| `/status` | 返回 ESP32 IP、WiFi 状态和时间 |
| `/update` | 触发刷新，返回 `QUEUED` |
| `/restart` | 重启 ESP32 |

## Obsidian 任务格式

脚本读取未完成任务：

```markdown
- [ ] 示例任务 ⏫ 🛫 2026-07-05 📅 2026-07-06
```

支持优先级标记：

- `⏫` 最高
- `🔺` 高
- `🔼` 中高
- `🔽` / `⏬` 低

支持日期：

- `🛫 YYYY-MM-DD` 开始日期
- `📅 YYYY-MM-DD` 截止日期

## 供电与故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `ESP32 离线` | ESP32 未联网、IP 变动或供电异常 | 先访问 `http://<ESP_IP>/status` |
| 拔 USB 后网页打不开 | 电池切换后没有干净启动 | 按 RST/EN，或换稳定供电 |
| 刷新中 ESP32 暂时无响应 | 墨水屏刷新期间 WiFi 会短暂阻塞 | 等待刷新完成 |
| 刷新后长期离线 | 电池/升压模块瞬时电流不足 | 用充电宝/稳定 5V，或加 470uF~1000uF 电容 |
| 屏幕全黑/花屏 | 图像格式、屏幕型号或引脚不匹配 | 检查 `EPD_W`、`EPD_H`、颜色编码和接线 |

## 安全说明

公开仓库不要提交：

- `config.json`
- `src/config.h`
- 日志文件
- PlatformIO 构建目录 `.pio/`

这些已在 `.gitignore` 中排除。
