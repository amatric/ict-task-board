# 智能行程规划 MCP Server + 高德实时路线

华为 ICT 大赛云赛道 **赛题7（MCP-智能行程规划）** 的参评作品。

组成三块：**高德 MCP 配置** + **自研行程规划 MCP Server（4 个工具）** + **可缩放实时路线图前端**。

## 目录

```
.
├── mcp_settings.json        # 同时挂载 高德官方MCP(amap-maps) 与 自研 trip-planner
├── config.example.json      # 高德 Key 配置模板（config.json 不入库）
├── server.py                # 自研 MCP Server（stdio JSON-RPC，4 工具）
├── server/amap_client.py    # 真实调用高德 Web API：地理编码 / 驾车 / 步行
├── web/index.html           # 高德 JS API 可缩放地图 + 路线折线
├── client_demo.py           # MCP 客户端演示
└── MCP-智能行程规划实践.md    # 实践文档
```

## 快速开始

```bash
# 1) 配置高德 Key
cp config.example.json config.json && vi config.json

# 2) 验证真实调用
python3 server/amap_client.py geo 故宫 北京

# 3) 起前端看可缩放实时路线图
python3 -m http.server 8000     # 打开 http://localhost:8000/web/index.html

# 4) 验证 MCP 协议
python3 client_demo.py
```

## 高德接入证据

- `mcp_settings.json` 配置了 `amap-maps`（高德官方 MCP，`@amap/amap-maps-mcp-server`）
- `server/amap_client.py` 真实请求 `/v3/geocode/geo`、`/v3/direction/driving`、`/v3/direction/walking`
- `web/index.html` 加载高德 JS API 2.0，绘制驾车路线 polyline，支持缩放与拖拽

详见 [MCP-智能行程规划实践.md](MCP-智能行程规划实践.md)。
