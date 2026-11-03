# 智能行程规划 MCP Server

华为 ICT 大赛云赛道 **赛题7（MCP-智能行程规划）** 的参评作品。

一个**零第三方依赖**的 MCP（Model Context Protocol）Server，用 stdio JSON-RPC 2.0 暴露 4 个行程规划工具，可被任意 MCP 客户端（码道 / Claude Desktop / 自研 Agent）直接挂载。

## 协议实现

实现了 MCP 标准的四个方法：

| 方法 | 作用 |
|:--|:--|
| `initialize` | 握手，返回 `protocolVersion` / `serverInfo` / `capabilities.tools` |
| `notifications/initialized` | 通知，无响应 |
| `tools/list` | 返回工具清单与 `inputSchema`（JSON Schema） |
| `tools/call` | 执行工具，结果包成 `content[{type:"text"}]` + `isError` |

错误码遵循 JSON-RPC 2.0：`-32700` 解析失败、`-32601` 方法不存在、`-32602` 参数错误。

## 4 个工具

### 1. `search_attractions`
按城市 + 偏好检索景点。

```json
{"city": "成都", "preference": "自然", "limit": 5}
```

### 2. `plan_itinerary`
按天数与偏好生成逐日行程，每天控制在约 7 小时游览内，返回总门票。

```json
{"city": "成都", "days": 3, "preferences": ["自然", "美食"]}
```

偏好打分：景点 `tags` 命中偏好越多排序越靠前。

### 3. `estimate_budget`
按人数 / 天数 / 档位估算预算，给出住宿、餐饮、市内交通、门票四类明细与人均。

```json
{"days": 3, "people": 2, "tier": "舒适", "ticket": 80}
```

档位：`经济` / `舒适` / `豪华`，酒店按 `days-1` 晚计，3 人以上按两间房估算。

### 4. `plan_trip`（组合工具）
一次调用完成「检索 → 排程 → 预算」，并给出一句话结论：

```json
{"city": "成都", "days": 3, "people": 2, "tier": "舒适", "preferences": ["自然", "美食"]}
```

返回 `itinerary` + `budget` + `summary`，适合让 Agent 一步拿到完整方案。

## 接入方式

MCP 客户端配置（以 Claude Desktop / 码道为例）：

```json
{
  "mcpServers": {
    "trip-planner": {
      "command": "python3",
      "args": ["/绝对路径/mcp-trip-planner/server.py"]
    }
  }
}
```

也可以手动喂 JSON-RPC 验证：

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 server.py
```

## 自测

```bash
python3 client_demo.py
```

会依次完成：`initialize` 握手 → `tools/list` 列工具 → `tools/call` 调 `plan_trip`，把完整方案打印出来。

实际输出片段：

```
== tools/call: plan_trip ==
{
  "ok": true,
  "city": "成都",
  "days": 3,
  "people": 2,
  "itinerary": [
    {"day": 1, "total_hours": 5, "items": [{"name": "都江堰", ...}]},
    ...
  ],
  "budget": {"tier": "舒适", "total": 3315, "per_person": 1657.5, ...},
  "summary": "成都 3 天 2 人（舒适档）共 15 小时游览，预算约 ¥3315，人均 ¥1657.5"
}
```

## 设计取舍

- **不用 MCP SDK**：标准库直接实现协议，便于在任何环境零安装运行，也说明协议本身很薄
- **工具分层**：三个原子工具 + 一个组合工具，Agent 既可细粒度调用，也可一步拿结果
- **错误可读**：工具内部错误（如城市未收录）通过 `isError: true` 返回结构化 JSON，而不是抛异常中断会话
- **内置样例库**：北京/上海/成都各 5 个景点，保证可离线演示；替换为真实 POI 接口只需改 `ATTRACTIONS` 与 `search_attractions`

## 目录

```
.
├── server.py        # MCP Server（stdio JSON-RPC）
├── client_demo.py   # 客户端演示
└── README.md
```
