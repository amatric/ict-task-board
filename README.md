# 华为云服务 MCP Server

华为 ICT 大赛云赛道 **赛题8（MCP-如何将华为云服务封装成 MCP Server）** 的参评作品。

把华为云 **ECS / EVS / OBS** 的能力封装成标准 MCP 工具，任意 MCP 客户端（码道 / Claude Desktop / 自研 Agent）挂载后即可用自然语言查云资源。

## 为什么这样封装

| 设计点 | 说明 |
|:--|:--|
| **凭证从环境变量注入** | `HUAWEICLOUD_SDK_AK/SK/REGION`，代码与日志里永不出现密钥 |
| **单文件零依赖** | 标准库实现 stdio JSON-RPC 2.0，不需要 pip install 就能跑 |
| **错误结构化** | 云 API 报错包成 `{ok:false, error:{...}}` 并以 `isError:true` 返回，不中断会话 |
| **凭证缺失友好降级** | 没配凭证时返回 `need_credentials:true` + 修复提示，而不是抛异常 |
| **`mcp_settings.json` 就绪** | 直接可被客户端加载，无需再手写配置 |

## 四个工具

| 工具 | 作用 | 对应云服务 |
|:--|:--|:--|
| `hw_region_info` | 查看当前区域、端点、凭证就绪状态（不泄露密钥） | — |
| `hw_list_ecs` | 列出当前区域弹性云服务器 | ECS |
| `hw_list_evs` | 列出当前区域云硬盘 | EVS |
| `hw_list_buckets` | 列出对象存储桶 | OBS |

## 接入

`mcp_settings.json` 已给出标准配置：

```json
{
  "mcpServers": {
    "huaweicloud": {
      "command": "python3",
      "args": ["${workspaceFolder}/server.py"],
      "env": {
        "HUAWEICLOUD_SDK_AK": "${env:HUAWEICLOUD_SDK_AK}",
        "HUAWEICLOUD_SDK_SK": "${env:HUAWEICLOUD_SDK_SK}",
        "HUAWEICLOUD_SDK_REGION": "cn-north-4"
      }
    }
  }
}
```

手动验证：

```bash
# 列工具
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 server.py

# 查凭证状态（不需要真凭证，用于自检）
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"hw_region_info","arguments":{}}}' | python3 server.py

# 配好凭证后列 ECS
export HUAWEICLOUD_SDK_AK=... HUAWEICLOUD_SDK_SK=... HUAWEICLOUD_SDK_SECURITY_TOKEN=...
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hw_list_ecs","arguments":{"limit":5}}}' | python3 server.py
```

实际输出（`hw_region_info`）：

```json
{
  "ok": true,
  "region": "cn-north-4",
  "ak_configured": false,
  "sk_configured": false,
  "token_configured": false,
  "endpoints": {
    "ecs": "https://ecs.cn-north-4.myhuaweicloud.com",
    "obs": "https://obs.cn-north-4.myhuaweicloud.com"
  }
}
```

## 生产化建议

当前实现用 `X-Auth-Token` 直连各服务 REST 接口，便于演示与排查。生产环境建议：

1. 换成官方 SDK —— `huaweicloudsdkcore` + `huaweicloudsdkecs`，由 SDK 处理 AK/SK 签名（V4）
2. OBS 走 `obsutil` 或 `esdk-obs-python`，OBS 的签名与 ECS/EVS 不同
3. 增加分页与会话级缓存，避免 Agent 频繁调用打到限流
4. 用 IAM 委托 + STS 临时凭证替代长期 AK/SK，凭证 900 秒自动轮换

## 目录

```
.
├── server.py          # MCP Server（stdio JSON-RPC 2.0）
├── mcp_settings.json  # 客户端配置
└── README.md
```
