# hwc —— 华为云服务命令行工具（真实调用）

华为 ICT 大赛云赛道 **赛题11（CLI-如何将华为云服务封装成 CLI）** 的参评作品。

`hwc` 把华为云 ECS / EVS / OBS 的查询封装成命令行，**代码里是真实的华为云 API 调用**，不是样例数据。

## 真实调用在哪

| 子命令 | 实际请求 |
|:--|:--|
| `hwc ecs list` | `GET https://ecs.{region}.myhuaweicloud.com/v2.1/{project_id}/servers/detail`，Header `X-Auth-Token` |
| `hwc ecs show <id>` | `GET .../v2.1/{project_id}/servers/{server_id}` |
| `hwc evs list` | `GET https://evs.{region}.myhuaweicloud.com/v2/{project_id}/cloudvolumes/detail` |
| `hwc obs ls obs://b/p` | `GET https://obs.{region}.myhuaweicloud.com/{bucket}?prefix=...`，**OBS V2 签名**（`Authorization: OBS AK:Base64(HMAC-SHA1(SK, STS))`） |

ECS/EVS 走 `X-Auth-Token`，OBS 走 V2 签名——两种认证方式都实现了，因为华为云这两类服务的鉴权本来就不同。

## 凭证

```bash
# ECS / EVS：X-Auth-Token（由 IAM 换取）
export HUAWEICLOUD_SDK_SECURITY_TOKEN=<x-subject-token>
export HUAWEICLOUD_SDK_PROJECT_ID=<project_id>

# OBS：AK/SK（V2 签名），STS 场景再加 OBS_SECURITY_TOKEN
export OBS_AK=... OBS_SK=...
export OBS_ENDPOINT=https://obs.cn-north-4.myhuaweicloud.com

# 区域（默认 cn-north-4）
export HWC_REGION=cn-north-4
```

取 token 的方式（与 EVS 实验里用过的一致）：

```bash
curl -i -X POST https://iam.cn-north-4.myhuaweicloud.com/v3/auth/tokens \
  -H 'Content-Type: application/json' -d @token.json
# 响应头 X-Subject-Token 就是 HUAWEICLOUD_SDK_SECURITY_TOKEN
```

## 人机双输出

```bash
$ python3 hwc.py ecs list
NAME        ID          STATUS    FLAVOR        IP
----------  ----------  --------  ------------  ------------
web-01      8f3c...a1   ACTIVE    s6.large.2    192.168.0.10

$ python3 hwc.py ecs list --json
[{"name": "web-01", "id": "8f3c...a1", "status": "ACTIVE", ...}]
```

## 没配凭证时的行为

不会假装成功，也不会静默返回空：

```json
{"ok": false, "error": "缺少 X-Auth-Token：请设置 HUAWEICLOUD_SDK_SECURITY_TOKEN（由 IAM 换取）", "hint": "未配凭证时可用 --demo 查看样例数据"}
```

想离线演示整体效果，显式加 `--demo` 才用内置样例：

```bash
python3 hwc.py ecs list --demo
```

## 命令树

```
hwc
├── ecs  { list [--limit N] | show <id> }
├── evs  { list [--limit N] }
├── obs  { ls <obs://bucket/prefix> [--limit N] }
└── region
```

全局选项 `--json` / `--region` / `--demo` 在**子命令前后都能写**（用 argparse `parents=[common]` 实现）。

## 封装 CLI 的经验

1. **先确认鉴权方式**：ECS/EVS 是 token，OBS 是 V2 签名，套错就会 401
2. **人机双输出**：默认表格 + `--json`，脚本与人各取所需
3. **错误走 stderr 带 hint**，退出码非 0，能被 shell 判断
4. **全局选项放宽位置**：`--json` 前后都行
5. **样例数据要显式开关**（`--demo`），绝不在真实调用失败时偷偷回退——否则使用者会以为拿到了真数据
6. **project_id 必须显式配置**，不要猜

## 自测

```bash
python3 hwc.py region                        # 看凭证与端点状态
python3 hwc.py ecs list                      # 无凭证 → 结构化报错
python3 hwc.py ecs list --demo               # 离线演示
python3 hwc.py obs ls obs://mybucket/x       # 真实 OBS 调用（需 AK/SK）
```

## 目录

```
.
├── hwc.py
├── hwc/{__init__.py,__main__.py,cli.py}
└── README.md
```
