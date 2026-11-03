# MCP · 智能行程规划实践

> 华为 ICT 大赛云赛道 赛题7 实践文档
> 构成：高德 MCP 配置 + 自研行程规划 MCP Server + 可缩放实时路线图前端

## 一、整体架构

```
前端 web/index.html（高德 JS API，可缩放地图）
        │  路线规划按钮
        ▼
高德开放平台 Web 服务 API（geocode / direction/driving）
        ▲
        │  由 server/amap_client.py 调用
自研 MCP Server（server.py，4 个工具）
        ▲
        │  stdio JSON-RPC
MCP 客户端（码道 / Claude Desktop）
        ▲
        │ 同时挂载
高德官方 MCP（amap-maps，见 mcp_settings.json）
```

两条入口并存：**行程规划用自研工具，POI/地理编码可直接走官方高德 MCP**。

## 二、高德接入（本题硬要求）

### 2.1 Key 配置

复制 `config.example.json` 为 `config.json`：

```json
{
  "amap": {
    "web_key": "<Web服务 Key>",
    "js_key": "<Web端(JS API) Key>",
    "security_code": "<如开启安全密钥则填>"
  }
}
```

也可用环境变量：`AMAP_WEB_KEY`、`AMAP_MAPS_API_KEY`。

### 2.2 高德 MCP 配置（mcp_settings.json）

```json
{
  "mcpServers": {
    "amap-maps": {
      "command": "npx",
      "args": ["-y", "@amap/amap-maps-mcp-server"],
      "env": { "AMAP_MAPS_API_KEY": "${env:AMAP_MAPS_API_KEY}" }
    },
    "trip-planner": {
      "command": "python3",
      "args": ["${workspaceFolder}/server.py"]
    }
  }
}
```

### 2.3 真实调用高德 API

`server/amap_client.py` 实际请求三个接口：

| 接口 | 用途 | 返回 |
|:--|:--|:--|
| `/v3/geocode/geo` | 地址 → 经纬度 | `lng` / `lat` / 格式化地址 |
| `/v3/direction/driving` | 驾车路线 | 距离、耗时、**polyline 折线点串**、分步指令 |
| `/v3/direction/walking` | 步行路线 | 距离、耗时、polyline |

```python
from server.amap_client import geocode, driving_route
p = geocode("故宫", "北京")            # {'lng': 116.397, 'lat': 39.918, ...}
r = driving_route("116.391,39.907", "116.403,39.937")
print(r["distance_m"], r["duration_s"], len(r["polyline_points"]))
```

Key 缺失时的行为是**明确报错**而不是静默失败：

```
{"ok": false, "error": "未配置高德 Web 服务 Key。请复制 config.example.json 为 config.json 并填写 amap.web_key"}
```

## 三、可缩放实时路线图

`web/index.html`：

- 加载高德 **JS API 2.0**（`webapi.amap.com/maps?v=2.0&key=...`）
- 深色底图（`amap://styles/darkblue`）
- 三个景点 Marker，`map.setFitView()` 自动缩放到全部可见
- 点「规划路线」调 `AMap.Driving`，在地图上**绘制真实路线折线**，并回填距离与预计耗时
- 地图本身支持滚轮缩放、拖拽平移
- 未配 Key 时给出配置指引，不白屏

运行：

```bash
python3 -m http.server 8000
# 打开 http://localhost:8000/web/index.html
```

## 四、自研行程规划 MCP 工具（本地逻辑）

| 工具 | 作用 |
|:--|:--|
| `search_attractions` | 按城市/偏好检索景点 |
| `plan_itinerary` | 按天数与偏好排逐日行程（每天 ≤ 约 7 小时） |
| `estimate_budget` | 按人数/天数/档位估算预算与分类明细 |
| `plan_trip` | 组合：检索 → 排程 → 预算 → 一句话结论 |

这几个工具不依赖网络，负责"排程与算账"；高德负责"地理与路线"。职责分明。

## 五、验收清单

| 检查 | 方式 |
|:--|:--|
| 高德 Key 已配置 | `config.json` 存在且 `amap.web_key` 非占位 |
| 真实调用高德 | `python3 server/amap_client.py geo 故宫 北京` 返回经纬度 |
| 路线折线 | 页面点「规划路线」后地图出现蓝色路线 |
| 地图可缩放 | 滚轮缩放、拖拽平移 |
| MCP 可挂载 | `mcp_settings.json` 中含 `amap-maps` 与 `trip-planner` |
| 自研工具可用 | `python3 client_demo.py` 走完 initialize → tools/list → tools/call |

## 六、设计取舍

- **两条 MCP 并行**：官方高德 MCP 覆盖 POI/地理编码，自研工具覆盖排程与预算，避免把所有逻辑塞进一个 Server
- **前端独立静态页**：不引入构建链，`python3 -m http.server` 即可演示
- **Key 绝不入仓**：`config.json` 进 `.gitignore`，仓库只有 `config.example.json`
- **无 Key 可降级演示**：自研 MCP 工具与 `--demo` 路径不依赖高德，保证离线也能看效果
